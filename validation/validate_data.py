"""Quick, standalone data validation for the waiting-list dataset. Run any
time -- takes a few seconds. Not a prompting exercise -- just run it.

Run it with:  python validation/validate_data.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pandera.polars as pa
from databricks_helpers import CACHE_PATH, load_waiting_list

schema = pa.DataFrameSchema(
    {
        "Hospital": pa.Column(str, pa.Check.isin([
            "Glangwili General Hospital",
            "Withybush General Hospital",
            "Prince Philip Hospital",
            "Bronglais General Hospital",
        ]), nullable=False),
        "Specialty": pa.Column(str, nullable=False),
        # coerce=True: tested finding -- Days_Waiting can come back as Polars Int32
        # or Int64 depending on the source (e.g. a plain VALUES-clause round trip vs.
        # cur.fetchall() -> pl.DataFrame(..., orient="row")), and pandera.polars
        # fails strictly on an exact dtype mismatch rather than any-integer-width.
        # coerce=True avoids a false-positive validation failure over bit width,
        # which isn't a real data-quality issue.
        "Days_Waiting": pa.Column(int, pa.Check.ge(0), nullable=False, coerce=True),
        "Priority": pa.Column(str, pa.Check.isin(["Routine", "Urgent", "2-Week Wait"]), nullable=False),
        "Pathway": pa.Column(str, pa.Check.isin(["RTT", "2WW"]), nullable=False),
    }
)


def main() -> None:
    if not CACHE_PATH.exists():
        raise SystemExit(
            f"{CACHE_PATH} not found -- run scripts/databricks_setup.py first."
        )

    df = load_waiting_list()

    try:
        schema.validate(df, lazy=True)
    except pa.errors.SchemaErrors as err:
        print("[FAILED] Validation errors found:\n")
        print(err.failure_cases)
        raise SystemExit(1)

    print(f"[ok] All validation checks passed ({df.height} rows).")


if __name__ == "__main__":
    main()
