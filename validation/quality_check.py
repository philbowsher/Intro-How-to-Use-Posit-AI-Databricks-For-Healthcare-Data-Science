"""Quick sanity-check summary of the waiting-list dataset -- a final
gut-check before you present results. Run any time; no extra packages
beyond what check_packages.py already installs.

Run it with:  python validation/quality_check.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import polars as pl
from databricks_helpers import CACHE_PATH, RTT_THRESHOLD, load_waiting_list


def main() -> None:
    if not CACHE_PATH.exists():
        raise SystemExit(
            f"{CACHE_PATH} not found -- run scripts/databricks_setup.py first."
        )

    df = load_waiting_list()

    print("=== Quick Quality Check ===\n")

    neg_days = df.filter(pl.col("Days_Waiting") < 0).height
    print(f"{'[ok]     ' if neg_days == 0 else '[warning]'} No negative wait times ({neg_days} found)")

    n_hospitals = df.get_column("Hospital").n_unique()
    n_specialties = df.get_column("Specialty").n_unique()
    print(f"[info]    {n_hospitals} hospitals, {n_specialties} specialties, {df.height} rows total")

    breaches = df.filter(pl.col("Days_Waiting") > RTT_THRESHOLD).height
    print(f"[info]    {breaches} rows breach the {RTT_THRESHOLD}-day RTT threshold "
          f"({100 * breaches / df.height:.1f}%)")

    print("\nIf anything above looks wrong, dig into it before presenting your results.")


if __name__ == "__main__":
    main()
