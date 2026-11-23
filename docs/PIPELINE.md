# gudi: dry-run production queue for Gudi Kathalu (EP02-06)

Set up 23 Nov 2026. **Nothing was bought, no narration was synthesised, the scheduler is off,
nothing was published.** The approved EP01 cut and `publishing/ep01/` are untouched (hashes
checked before and after).

## Real entry points it reuses

| Need | Existing entry point | How gudi uses it |
|---|---|---|
| Generation settings | `config/production.json` | Untouched. Stills are nano_banana_2 at 2k, clips Kling 3.0 pro with sound off |
| Higgsfield | The Higgsfield MCP connector (no client code exists in the repo) | `gudi/paid/higgsfield.py` calls it through Claude Code print mode (`claude -p`), allowing exactly one generation tool per call |
| Narration download | `scripts/fetch-narration.sh` (Speech History; the CLI login lives in `.env.local`) | `gudi/paid/elevenlabs.py` uses it to fetch and to recover a take |
| Render | `node scripts/render.mjs` (Mac) and the Python/FFmpeg assembly in `scripts/ep01_full/` | Not called yet: EP02 has no composition. The review export marks the film as pending |
| Spend limits (new) | `config/pipeline.json` | Daily and monthly cap per provider. All caps start unset, which means no spending |

## The five scripts (Voice sections only, verbatim)

| Slot | Path | Words | sha256 |
|---|---|---|---|
| EP02 | `episodes/ep02-kolanupaka/voice.te.txt` | 183 | 35da0719cb3a... |
| EP03 | `episodes/ep03-vemulavada/voice.te.txt` | 162 | 949200ba5e85... |
| EP04 | `episodes/ep04-srikalahasti/voice.te.txt` | 146 | 8bfe42d699ae... |
| EP05 | `episodes/ep05-yadagirigutta/voice.te.txt` | 159 | b7e4ad325a1a... |
| EP06 | `episodes/ep06-kanipakam/voice.te.txt` | 142 | 82df3eb993c2... |

The importer checks that each script is an exact substring of the book
(`source-docs/Gudi_Kathalu_EP02-06_Production_Book.md`). Kept separately in each folder:
`cover.te.txt`, `directions.json` (beat directions and evidence), `sources.json`, and
`episode.json` (status: draft, awaiting editorial approval). **No Telugu edits are proposed.**
Each `proposed-edits.diff` is empty. Queue order is in `episodes/queue.json`, and EP02 is next.

## EP02

- `episodes/ep02-kolanupaka/reference-board.json`: each reference with identity, URL, use,
  rights and status. EP01 artwork appears only as **style** references.
- `episodes/ep02-kolanupaka/shots.json`: 17 on-screen shots plus 2 character sheets. Each is
  tied to the exact spoken words, timed provisionally at EP01's measured rate (about 99 s).
- `storyboard.md` and `cost-sheet.md` are generated from the two files above
  (`python3 -c "from gudi.storyboard import render; render('ep02-kolanupaka')"`).

**Cost by provider (quotes only):**

| Provider | Full plan | Unblocked today |
|---|---|---|
| Higgsfield | **72 credits**: 15 stills x 2 = 30, plus 6 clips, 28 s in all = 42 | 6 (S03 villagers, S07 ashram, S16 stone) |
| ElevenLabs | **about 1,430 credits**: one take of 1,430 characters at EP01's logged rate of 1 credit per character per take. Provisional, because the connector can't quote on this account | 1,430 |

Repairs are not included and nothing is reserved for them; each one needs your explicit retry approval.

**Unresolved, explicitly blocking 18 of the 21 Higgsfield calls:**
- **K-LINGA:** no identified image of the Swayambhu Someshwara linga. A 2018 report describes
  it as cracked, and one listing says photography isn't allowed inside.
- **K-RENUKA:** no chosen iconographic reference for Renukacharya. Also a naming check:
  some listings call the shrine "Someshwara Revanasiddeshwara".
- **K-AGASTYA:** no chosen reference for Agastya and Lopamudra.
- **K-EXTERIOR:** a lead only. The Kaladarshana page (copyright Amit Guha) is labelled
  Someswara Temple, but it's for reference only and needs your confirmation. The Heritage
  Telangana page (K2) could not be fetched from here.

## How the paid path is guarded

- **Approval** (`gudi approve`, a human command) pins the script hash, a hash of the reference
  board plus the shot list, the voice, and a per-provider episode cap. Editing any of them
  makes it stale, and the runner holds.
- **Budget check:** before anything is reserved, the whole remaining unblocked plan must fit
  under every limit: the episode cap, the daily cap, the monthly cap and the recorded balance
  (minus spend since it was recorded). Otherwise the episode is held whole. There is no
  partial spending.
- **Ledger** (`state/ledger.sqlite3`, gitignored):
  - Each request gets a stable key: a hash of episode, revision, beat, asset type, prompt,
    references, model and settings.
  - Credits are stored as exact integer milli-credits.
  - The full quote is reserved in a transaction before submission.
  - The row is marked `submitting` and committed before the provider is called.
  - A recorded job ID means resume is a poll. A missing ID means reconcile against provider
    history; if the job isn't found, the row is held as `unknown` with its reservation until a
    person runs `gudi reconcile`.
  - Failed requests are never retried automatically.
- **Locks:** one runner at a time (file lock), and one episode per local day (Asia/Kolkata,
  held in the ledger). A missed day never triggers a catch-up.
- **Dry run:** `gudi queue` and `gudi run --dry-run` set `GUDI_DRY_RUN=1`, and nothing on
  those paths imports `gudi/paid/`. That package also refuses to import under the flag.
- **Unattended runner:** only `python3 -m gudi daily`. It can't edit approvals or caps,
  publish, or retry, and its Claude calls are limited to the Higgsfield generate and
  show-generations tools.
- **Review export** (`review/<episode>/<date>/`) contains a manifest, a cost file (quoted,
  settled and still reserved per provider), captions, the cover, a platform text draft,
  and the film or a note that it's pending. Posting stays your decision.

## Commands

The exact dry-run command (from the repo root on your Mac):

```
/usr/bin/python3 -m gudi queue
```

Its output today is in `docs/PIPELINE-DRYRUN-OUTPUT.txt`. It ends with:
`NEXT: ep02-kolanupaka (not eligible yet; see 'missing' above). Exiting cleanly, nothing spent.`

| Command | Effect |
|---|---|
| `python3 -m gudi demo` (or `python3 -m unittest tests.test_gudi`) | Mock demonstrations, transcript in `docs/PIPELINE-DEMO-OUTPUT.txt`, all passing |
| `python3 -m gudi daily` | Today: `PENDING ep02-kolanupaka: script, look and budget not approved. Nothing spent.` |
| `python3 -m gudi schedule print` | Shows the manual command and the LaunchAgent plist |
| `python3 -m gudi schedule install` | Refuses while `schedule.enabled` is false, and needs `--yes` even then |
| `python3 -m gudi balance record higgsfield 356.05 --as-of 2026-11-23T23:05:00+05:30` | Records a balance with its date. Today's 356.05 was read from the connector by Claude, not supplied by you. `state/` is gitignored, so re-record it on the Mac |

## Mock demonstrations (summary)

| Scenario | Result |
|---|---|
| No approved episode | Pending item printed, exit 0, 0 paid calls |
| Insufficient budget (cap 5, plan 11.5), and caps unset | Held before any reservation, 0 paid calls |
| Duplicate launch | Second launch refused while the first held the lock. The first paid exactly 4 requests. A second episode the same day waits |
| Crash right after submission | Resume found the job in provider history and didn't resubmit: 4 receipts in total |
| Crash after submission, job not in history | Held as `unknown` with its reservation and never resent. After a person attached the job ID, it completed with 4 receipts |
| Crash after download | Resume re-fetched the file only, with no new charge |
| Second identical run | 0 new charges |
| Dry run | `gudi.paid` never imported; importing it under a dry run raises `ImportError` |

## What the first paid run needs from you

1. **References:** confirm or supply K-LINGA, K-RENUKA, K-AGASTYA and K-EXTERIOR, or approve
   a plan that drops the shots needing them. Then set each one to `verified` on the board.
2. **Script and look:** approve the EP02 Voice text as-is (no edits proposed) and the board
   plus shot list.
3. **Caps:** a Higgsfield episode cap (the plan quotes 72; repairs would need more, each
   approved separately) and an ElevenLabs episode cap (about 1,430). Also daily and monthly
   caps per provider in `config/pipeline.json`.
4. **Balances:** confirm the Higgsfield balance and supply the ElevenLabs one. The connector
   can't read it on this account.
5. **Then** run on the Mac:
   `python3 -m gudi approve ep02-kolanupaka --by Karunakar --cap higgsfield=<N> --cap elevenlabs=<N> --i-have-reviewed`
6. **First live run, supervised and at the keyboard:**
   `python3 -m gudi run --episode ep02-kolanupaka --live`. It starts with the narration. After
   the take, timings and clip lengths get re-derived; that edits `shots.json`, which makes the
   approval stale on purpose, so the revised quote is approved again before any clip is bought.

## Not yet proven

- The live Higgsfield and ElevenLabs adapters have **not been exercised**. Two assumptions get
  confirmed on the first supervised call: the MCP server name `claude -p` sees on your Mac
  (`mcp_server` in `config/pipeline.json`), and that ElevenLabs returns a `history-item-id` header.
- Live reconciliation is manual for now: an `unknown` row is resolved with `gudi reconcile`
  after checking `show_generations` or `sh scripts/fetch-narration.sh`.
- EP02's render step (the composition) is not built, so the daily review export will list
  the film as pending until it is.
- The scheduler is off. Enabling it means `schedule.enabled: true`, caps set, a manual
  `python3 -m gudi daily` first, then `schedule install --yes`. The Mac has to be awake,
  online and signed in at the set time.
