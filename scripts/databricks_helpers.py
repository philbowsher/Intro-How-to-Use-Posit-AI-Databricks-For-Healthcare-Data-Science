"""Shared Databricks connection + query logic for this workshop.

Deterministic, tested plumbing -- don't ask Posit Assistant to regenerate
this module. It exists so the four working documents (new_analysis.qmd,
Dashboard.qmd, app.py, app_streamlit.py) don't each re-paste the same
~15-line connect/query/schema block (which is what solutions/ currently
does). Ask Assistant to build charts/filters/KPIs from the DataFrame this
returns -- that's the actual workshop exercise.

Standardized schema (all four workflows use this same shape -- note this
replaces two slightly-different schemas that existed across the current
solutions/ files before this rebuild):

    Hospital      (str)  -- one of 4 NHS Wales hospital sites
    Specialty     (str)  -- e.g. "Cardiology", "Orthopaedics"
    Days_Waiting  (i64)  -- referral-to-treatment wait, in days
    Priority      (str)  -- "Routine" | "Urgent" | "2-Week Wait"
    Pathway       (str)  -- "RTT" | "2WW"

20 rows, 4 hospitals x up to 5 specialties. This is a VALUES-clause query --
no data upload or external storage needed, and it's fully reproducible
from the SQL text below.
"""

import os
from pathlib import Path

import polars as pl

CACHE_PATH = Path("data/waiting_list.parquet")

SCHEMA = ["Hospital", "Specialty", "Days_Waiting", "Priority", "Pathway"]

WAITING_LIST_QUERY = """
SELECT * FROM (VALUES
    ('Glangwili General Hospital', 'Cardiology',    42,  'Urgent',      'RTT'),
    ('Glangwili General Hospital', 'Orthopaedics',  140, 'Urgent',      'RTT'),
    ('Glangwili General Hospital', 'Urology',        67, 'Routine',     'RTT'),
    ('Glangwili General Hospital', 'Dermatology',    89, 'Routine',     'RTT'),
    ('Glangwili General Hospital', 'Oncology',       12, '2-Week Wait', '2WW'),
    ('Withybush General Hospital', 'Orthopaedics',  118, 'Routine',     'RTT'),
    ('Withybush General Hospital', 'Cardiology',     65, 'Urgent',      'RTT'),
    ('Withybush General Hospital', 'Urology',       134, 'Routine',     'RTT'),
    ('Withybush General Hospital', 'Dermatology',    45, 'Routine',     'RTT'),
    ('Withybush General Hospital', 'Oncology',        9, '2-Week Wait', '2WW'),
    ('Prince Philip Hospital',     'Cardiology',     15, 'Routine',     'RTT'),
    ('Prince Philip Hospital',     'Orthopaedics',   92, 'Routine',     'RTT'),
    ('Prince Philip Hospital',     'Urology',        78, 'Urgent',      'RTT'),
    ('Prince Philip Hospital',     'Dermatology',    55, 'Routine',     'RTT'),
    ('Prince Philip Hospital',     'Oncology',        6, '2-Week Wait', '2WW'),
    ('Bronglais General Hospital', 'Cardiology',     22, 'Routine',     'RTT'),
    ('Bronglais General Hospital', 'Oncology',        8, '2-Week Wait', '2WW'),
    ('Bronglais General Hospital', 'Orthopaedics',  156, 'Routine',     'RTT'),
    ('Bronglais General Hospital', 'Urology',        98, 'Routine',     'RTT'),
    ('Bronglais General Hospital', 'Dermatology',    33, 'Urgent',      'RTT')
) AS t(hospital_site, specialty, days_waiting, priority_level, pathway)
"""

RTT_THRESHOLD = 126  # NHS 18-week referral-to-treatment target, in days


class DatabricksConnectionError(RuntimeError):
    """Raised when we can't reach Databricks -- wraps the underlying error
    with a message pointing at the likely fix rather than a raw traceback.
    """


def check_env() -> None:
    """Safety net: confirm .env has what we need before attempting a live
    connection, so a missing credential surfaces as a clear message instead
    of a confusing failure three calls deep into the databricks-sql-connector
    stack.
    """
    from dotenv import load_dotenv

    load_dotenv()
    missing = [
        var
        for var in ("DATABRICKS_HOST", "DATABRICKS_HTTP_PATH", "DATABRICKS_TOKEN")
        if not os.environ.get(var)
    ]
    if missing:
        raise DatabricksConnectionError(
            f"Missing from .env: {', '.join(missing)}. Copy .env.example to .env and fill in "
            "your Databricks credentials (see README.md Setup section), then try again."
        )


def query_databricks(query: str = WAITING_LIST_QUERY, schema: list[str] = SCHEMA) -> pl.DataFrame:
    """Connect to Databricks, run `query`, return a Polars DataFrame with
    the given column names. Raises DatabricksConnectionError with a clear
    message on connection failure, rather than letting the underlying
    exception surface as-is.
    """
    check_env()
    from databricks import sql

    try:
        conn = sql.connect(
            server_hostname=os.environ["DATABRICKS_HOST"],
            http_path=os.environ["DATABRICKS_HTTP_PATH"],
            access_token=os.environ["DATABRICKS_TOKEN"],
        )
    except Exception as e:
        raise DatabricksConnectionError(
            f"Could not connect to Databricks: {e}\n"
            "Check: is your SQL Warehouse running (not 'Stopped')? Are DATABRICKS_HOST and "
            "DATABRICKS_HTTP_PATH copied correctly from the warehouse's Connection Details page? "
            "Has your Personal Access Token expired?"
        ) from e

    try:
        with conn.cursor() as cur:
            cur.execute(query)
            df = pl.DataFrame(cur.fetchall(), schema=schema, orient="row")
    finally:
        conn.close()

    return df


def load_waiting_list(use_cache: bool = True, refresh: bool = False) -> pl.DataFrame:
    """Load the NHS Wales waiting-list dataset. By default reads the local
    cache written by `scripts/databricks_setup.py` (fast, no live Databricks
    connection needed) -- pass refresh=True to force a live re-query, or
    use_cache=False to always query live.

    This is what the four working documents should call, instead of each
    re-implementing connect + query + schema themselves.
    """
    if use_cache and not refresh and CACHE_PATH.exists():
        return pl.read_parquet(CACHE_PATH)

    df = query_databricks()

    if use_cache:
        CACHE_PATH.parent.mkdir(exist_ok=True)
        df.write_parquet(CACHE_PATH)

    return df
