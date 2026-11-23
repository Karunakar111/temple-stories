"""Project paths. GUDI_ROOT / GUDI_STATE override them (the mock demos use temp dirs)."""
import os
from pathlib import Path

ROOT = Path(os.environ.get("GUDI_ROOT", Path(__file__).resolve().parent.parent))
STATE = Path(os.environ.get("GUDI_STATE", ROOT / "state"))  # gitignored: ledger, locks
EPISODES = ROOT / "episodes"
CONFIG = ROOT / "config" / "pipeline.json"
PRODUCTION_CONFIG = ROOT / "config" / "production.json"
REVIEW = Path(os.environ.get("GUDI_REVIEW", ROOT / "review"))
BOOK = ROOT / "source-docs" / "Gudi_Kathalu_EP02-06_Production_Book.md"


def ensure_state():
    STATE.mkdir(parents=True, exist_ok=True)
    return STATE
