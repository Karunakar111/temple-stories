"""Persistent job ledger (SQLite, one file, transactional).

Every paid request moves through these states, and only forward:

  reserved   -> full quoted cost held against every applicable limit; nothing sent yet
  submitting -> committed BEFORE the provider is called; if we crash here, the request
                may or may not exist at the provider, so it must be reconciled, never resent
  submitted  -> provider job id recorded; resume = poll that id
  succeeded  -> provider says done; result URL known
  downloaded -> file on disk, checksum recorded; settled cost recorded
  failed     -> provider failed it; a new attempt needs `gudi retry --approve`
  unknown    -> reconciliation found nothing; reservation stays held until a human resolves it
  released   -> reservation returned (only by a human command or a pre-submit hold)

The request key is a hash of episode, revision, beat, asset type, prompt, references,
model and settings, so the same request can never be paid for twice by accident.
"""
import json
import sqlite3
import time
from datetime import datetime, timedelta, timezone

from .money import fmt

LIVE_STATES = ("reserved", "submitting", "submitted", "succeeded", "downloaded", "unknown")
SCHEMA = """
CREATE TABLE IF NOT EXISTS balances(
  id INTEGER PRIMARY KEY, provider TEXT NOT NULL, amount_milli INTEGER NOT NULL,
  as_of TEXT NOT NULL, source TEXT NOT NULL, recorded_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS jobs(
  request_key TEXT PRIMARY KEY, episode TEXT NOT NULL, revision TEXT NOT NULL,
  beat TEXT NOT NULL, asset_type TEXT NOT NULL, provider TEXT NOT NULL,
  params_json TEXT NOT NULL, quoted_milli INTEGER NOT NULL, settled_milli INTEGER,
  state TEXT NOT NULL, provider_job_id TEXT, result_url TEXT, local_path TEXT,
  sha256 TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, local_day TEXT NOT NULL,
  note TEXT);
CREATE INDEX IF NOT EXISTS jobs_ep ON jobs(episode);
CREATE TABLE IF NOT EXISTS day_locks(
  local_day TEXT PRIMARY KEY, episode TEXT NOT NULL, run_id TEXT NOT NULL, at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY, at TEXT NOT NULL, run_id TEXT, kind TEXT NOT NULL, detail TEXT);
"""


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def local_tz(cfg):
    # Asia/Kolkata has no DST; a fixed offset keeps this stdlib-only on Python 3.8.
    h, m = cfg.get("schedule", {}).get("utc_offset", "+05:30").lstrip("+").split(":")
    return timezone(timedelta(hours=int(h), minutes=int(m)))


class Ledger:
    def __init__(self, path):
        self.path = path
        self.db = sqlite3.connect(str(path), timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(SCHEMA)

    # ------------------------------------------------------------ helpers
    def tx(self):
        return _Tx(self.db)

    def event(self, kind, detail, run_id=None):
        self.db.execute(
            "INSERT INTO events(at, run_id, kind, detail) VALUES (?,?,?,?)",
            (now_utc(), run_id, kind, json.dumps(detail, ensure_ascii=False) if not isinstance(detail, str) else detail),
        )

    def job(self, key):
        return self.db.execute("SELECT * FROM jobs WHERE request_key=?", (key,)).fetchone()

    def jobs(self, episode=None):
        if episode:
            return self.db.execute("SELECT * FROM jobs WHERE episode=? ORDER BY created_at", (episode,)).fetchall()
        return self.db.execute("SELECT * FROM jobs ORDER BY created_at").fetchall()

    # ------------------------------------------------------------ balances
    def record_balance(self, provider, amount_milli, as_of, source):
        self.db.execute(
            "INSERT INTO balances(provider, amount_milli, as_of, source, recorded_at) VALUES (?,?,?,?,?)",
            (provider, amount_milli, as_of, source, now_utc()),
        )

    def last_balance(self, provider):
        return self.db.execute(
            "SELECT * FROM balances WHERE provider=? ORDER BY as_of DESC, id DESC LIMIT 1", (provider,)
        ).fetchone()

    # ------------------------------------------------------------ committed spend
    def committed(self, provider, episode=None, local_day=None, month=None, since=None):
        q = "SELECT COALESCE(SUM(COALESCE(settled_milli, quoted_milli)),0) FROM jobs WHERE provider=? AND state IN (%s)" % (
            ",".join("?" * len(LIVE_STATES))
        )
        args = [provider, *LIVE_STATES]
        if episode:
            q += " AND episode=?"
            args.append(episode)
        if local_day:
            q += " AND local_day=?"
            args.append(local_day)
        if month:
            q += " AND substr(local_day,1,7)=?"
            args.append(month)
        if since:
            q += " AND created_at>=?"
            args.append(since)
        return self.db.execute(q, args).fetchone()[0]

    def headroom(self, provider, episode, episode_cap, daily_cap, monthly_cap, local_day):
        """Remaining spend under every limit; None means the limit is not configured (=> no spend)."""
        bal = self.last_balance(provider)
        limits = {}
        limits["episode cap"] = None if episode_cap is None else episode_cap - self.committed(provider, episode=episode)
        limits["daily cap"] = None if daily_cap is None else daily_cap - self.committed(provider, local_day=local_day)
        limits["monthly cap"] = None if monthly_cap is None else monthly_cap - self.committed(provider, month=local_day[:7])
        limits["recorded balance"] = (
            None if bal is None else bal["amount_milli"] - self.committed(provider, since=bal["as_of"])
        )
        return limits

    # ------------------------------------------------------------ reservations
    def reserve(self, row, limits):
        """Insert a reservation only if the full quote fits under every limit. Atomic."""
        with self.tx():
            if self.job(row["request_key"]):
                return "exists"
            short = [k for k, v in limits.items() if v is None or v < row["quoted_milli"]]
            if short:
                return "insufficient: " + ", ".join(
                    f"{k} {'not set' if limits[k] is None else 'left ' + fmt(limits[k])}" for k in short
                )
            t = now_utc()
            self.db.execute(
                "INSERT INTO jobs(request_key, episode, revision, beat, asset_type, provider, params_json, quoted_milli,"
                " state, created_at, updated_at, local_day) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    row["request_key"], row["episode"], row["revision"], row["beat"], row["asset_type"],
                    row["provider"], row["params_json"], row["quoted_milli"], "reserved", t, t, row["local_day"],
                ),
            )
            return "reserved"

    def set_state(self, key, state, **fields):
        sets = ["state=?", "updated_at=?"]
        args = [state, now_utc()]
        for k, v in fields.items():
            sets.append(f"{k}=?")
            args.append(v)
        args.append(key)
        self.db.execute(f"UPDATE jobs SET {', '.join(sets)} WHERE request_key=?", args)

    # ------------------------------------------------------------ day lock
    def take_day(self, local_day, episode, run_id):
        with self.tx():
            row = self.db.execute("SELECT * FROM day_locks WHERE local_day=?", (local_day,)).fetchone()
            if row and row["episode"] != episode:
                return f"day {local_day} already belongs to {row['episode']}"
            if not row:
                self.db.execute(
                    "INSERT INTO day_locks(local_day, episode, run_id, at) VALUES (?,?,?,?)",
                    (local_day, episode, run_id, now_utc()),
                )
            return "ok"


class _Tx:
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        for _ in range(50):
            try:
                self.db.execute("BEGIN IMMEDIATE")
                return self
            except sqlite3.OperationalError:
                time.sleep(0.1)
        raise RuntimeError("ledger is locked")

    def __exit__(self, et, ev, tb):
        self.db.execute("ROLLBACK" if et else "COMMIT")
        return False
