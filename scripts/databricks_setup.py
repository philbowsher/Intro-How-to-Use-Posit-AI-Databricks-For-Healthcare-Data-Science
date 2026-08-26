"""Run this once, after check_packages.py and after filling in your .env,
to materialize the workshop dataset from Databricks into a local cache.

This is the "Phase 1: Connectivity" verification step -- if this script
runs cleanly, your .env credentials and warehouse are working, and every
downstream workflow (new_analysis.qmd, Dashboard.qmd, app.py,
app_streamlit.py) can read data/waiting_list.parquet instead of each
re-connecting to Databricks live.

Run it with:  python scripts/databricks_setup.py
Force a live re-query (e.g. after editing the VALUES clause in
scripts/databricks_helpers.py):  python scripts/databricks_setup.py --refresh

This is infrastructure, not a prompting exercise -- just run it.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from databricks_helpers import CACHE_PATH, DatabricksConnectionError, load_waiting_list


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force a live query against Databricks even if a cache already exists.",
    )
    args = parser.parse_args()

    if CACHE_PATH.exists() and not args.refresh:
        print(f"[skip]    {CACHE_PATH} already exists -- not re-querying. Use --refresh to force.")
        return

    print("Connecting to Databricks and running the waiting-list query...")
    try:
        df = load_waiting_list(use_cache=True, refresh=True)
    except DatabricksConnectionError as e:
        print(f"[FAILED]  {e}")
        raise SystemExit(1)

    print(f"[ok]      Connected to Databricks SQL Warehouse.")
    print(f"[ok]      Wrote {CACHE_PATH} ({df.height} rows, {df.width} columns)")
    print(f"          Columns: {', '.join(df.columns)}")
    print("\nYou're ready to start Workflow 1 (new_analysis.qmd).")


if __name__ == "__main__":
    main()
