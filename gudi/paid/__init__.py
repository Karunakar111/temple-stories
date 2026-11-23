"""Live, paid provider adapters.

This package refuses to import in a dry-run process. `gudi queue` and `gudi run --dry-run`
set GUDI_DRY_RUN=1 before doing anything, and nothing on those code paths imports this
package, so a dry run has no route to a paid call even by mistake.

Only `gudi run --live` (a person at the keyboard) and `gudi daily` (the scheduled runner,
which re-checks approval, caps and the day lock in code) can construct these adapters.
"""
import os

if os.environ.get("GUDI_DRY_RUN") == "1":
    raise ImportError("gudi.paid is unavailable in a dry run")
