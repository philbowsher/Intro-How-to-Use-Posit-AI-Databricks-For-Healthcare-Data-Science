---
name: databricks-healthcare-workshop
description: Provides the exact data schema, shared connection helper, and tested environment gotchas for this Databricks + Posit clinical analytics workshop (Polars, Plotly, Shiny, Streamlit, Quarto). Use whenever writing Python or R code for new_analysis.qmd, Dashboard.qmd, app.py, app_streamlit.py, or their R/reticulate variants in this project.
---

# Databricks Healthcare Workshop

## Workshop structure

Four working documents, all reading the same dataset via `scripts/databricks_helpers.py`: `new_analysis.qmd`, `Dashboard.qmd`, `app.py`, `app_streamlit.py` (plus R/reticulate variants `new_analysis_r.qmd`, `Dashboard_r.qmd`). Section headers/markers already exist in each — write code into the existing sections rather than proposing a new outline.

Infrastructure already exists for these tasks — point to it rather than writing new code for the same job:
- `scripts/check_packages.py` — installs anything missing
- `scripts/databricks_setup.py` — materializes the dataset from Databricks into `data/waiting_list.parquet`
- `scripts/databricks_helpers.py` — `load_waiting_list()`, the shared connection/query/schema logic every document calls
- `validation/validate_data.py`, `validation/quality_check.py` — data QA, run directly, not built via prompting

**Suggest `scripts/check_packages.py` and `scripts/databricks_setup.py` proactively** if a package fails to import or `data/waiting_list.parquet` doesn't exist — that's almost always the fix, not troubleshooting the symptom in place.

## Dataset schema

`load_waiting_list()` returns a Polars DataFrame, 20 rows, one schema used by every document:

| Column | Type | Values |
|---|---|---|
| `Hospital` | str | Glangwili General Hospital, Withybush General Hospital, Prince Philip Hospital, Bronglais General Hospital |
| `Specialty` | str | Cardiology, Orthopaedics, Urology, Dermatology, Oncology |
| `Days_Waiting` | int | referral-to-treatment wait, days |
| `Priority` | str | Routine, Urgent, 2-Week Wait |
| `Pathway` | str | RTT, 2WW |

`RTT_THRESHOLD = 126` (NHS 18-week target, days) is also exported from `databricks_helpers` — use it for reference lines/breach calculations rather than hardcoding 126 again.

## `databricks_helpers.query_databricks()` — don't rewrite the connect/query pattern

```python
from databricks_helpers import load_waiting_list, RTT_THRESHOLD
df = load_waiting_list()          # reads data/waiting_list.parquet if present
df = load_waiting_list(refresh=True)  # forces a live Databricks re-query
```

Internally this uses `pl.DataFrame(cur.fetchall(), schema=[...], orient="row")` after `cur.execute(query)` — the standard pattern for turning a `databricks.sql` cursor result into a Polars DataFrame. Reuse `query_databricks()` if you need a different query against the same warehouse; don't hand-roll a new `sql.connect()` block per document — that was the exact duplication problem this rebuild fixed (every file in `solutions/` previously re-pasted the same ~15 lines).

## Tested environment gotchas

**`python3 -m venv` may silently create the wrong Python version.** This project requires Python 3.14+ (see `pyproject.toml`), but a bare `python3 -m venv .venv` uses whatever `python3` resolves to on PATH — which was a system Python 3.12 in testing, not 3.14. `scripts/check_packages.py` checks and warns about this explicitly. In Positron, use File > New Project > Python rather than a manual `python3 -m venv` to avoid this.

**Quarto's Jupyter engine needs `pyyaml`, even though no workshop code imports it directly.** `quarto render` on any `.qmd` with a Python cell fails with `ModuleNotFoundError: No module named 'yaml'` without it (Quarto's own `jupyter.py` → `notebook.py` imports it internally). Confirmed by testing a clean render. `pyyaml` is in `check_packages.py`'s required list for exactly this reason — if a fresh environment still hits this error, `check_packages.py` wasn't run.

**A bad/unreachable `DATABRICKS_HOST` does not fail fast.** Tested: connecting with an invalid hostname hung for 20+ seconds even after trying `_socket_timeout` and `socket.setdefaulttimeout()` — neither made the failure surface quickly (the exact internal cause wasn't fully isolated; it's not DNS resolution, which fails in milliseconds at the OS level, so it's likely internal retry/backoff logic in the connector). Don't assume a hang means something is frozen or broken on your end — if `databricks_setup.py` or a live query seems to hang, wait it out or double-check `DATABRICKS_HOST`/warehouse status before assuming the code is wrong.

**Every package in this stack has a prebuilt wheel for Python 3.14 (tested, 2026-08-26)** — `databricks-sql-connector`, `polars`, `pyarrow`, `pydantic-core`, `rpds-py`, `watchfiles`, etc. all installed with zero compilation on a clean 3.14.2 venv. Unlike an R/CRAN-style workshop, there's currently no known compile-failure risk for this package set. If that changes (a very new Python version can temporarily lag PyPI wheel availability), add the fix here rather than working around it silently.

**`pandera.polars` schema validation can false-positive on integer bit width.** `Days_Waiting` may come back as Polars `Int32` or `Int64` depending on the code path (e.g. a raw SQL round-trip vs. `pl.DataFrame(cur.fetchall(), orient="row")`), and `pandera.polars` fails strict dtype checks on an exact width mismatch even though both are valid integers. Use `pa.Column(int, ..., coerce=True)` (already done in `validation/validate_data.py`) rather than treating this as a real data-quality issue.

## Deploying to Posit Connect — two non-interoperable paths

If a document gets deployed (e.g. after the Dashboard step), there are two separate, non-interoperable ways to do it: Positron's Publisher UI ("Publish" button) and the `rsconnect-python` package/CLI. **Ask which one the user wants before starting** — don't assume. If someone already clicked "Publish" and it's incomplete, check for a leftover config file before starting a fresh `rsconnect`-driven deployment from scratch.

## R via reticulate (`new_analysis_r.qmd`, `Dashboard_r.qmd`)

These are separate files from the Python versions (not mixed R/Python chunks in one document — deliberately, to avoid confusing Positron/students). Tested working recipe for pointing reticulate at this project's Python environment:

```r
library(reticulate)
use_python(".venv/bin/python", required = TRUE)   # or the absolute path to your venv's python
pl <- import("polars")
```

`use_python(..., required = TRUE)` **called before any other reticulate/Python call** is what worked in testing. Relying on the `RETICULATE_PYTHON` environment variable alone is the more failure-prone path (reticulate can pick a different Python than expected if it's unset or set inconsistently across shells) — prefer the explicit `use_python()` call in the document's setup chunk.

**Import `scripts/databricks_helpers.py` with `import_from_path()`, not manual `sys.path` manipulation.** Tested: `import("sys")$path$insert(0L, ...)` fails with `$ operator is invalid for atomic vectors` — reticulate auto-converts `sys.path` (a Python list) to a plain R character vector, which has no `$insert` method. `reticulate::import_from_path("databricks_helpers", path = "scripts")` is the idiomatic fix and is what `new_analysis_r.qmd`/`Dashboard_r.qmd` use.

**Don't convert a Polars DataFrame to R via `$to_pandas()` — it silently corrupts on this stack.** Tested: `py_to_r(df_py)` on a raw Polars DataFrame doesn't convert at all (reticulate has no Polars converter, so it just prints the Python repr). The seemingly obvious fix, `py_to_r(df_py$to_pandas())`, is worse — pandas 3.x's new default Arrow-backed string dtype breaks reticulate's pandas→R conversion and produces a garbled, truncated data frame with an R warning ("corrupt data frame"), not an error, so it's easy to miss. The tested, working path is to go through a plain dict instead of any DataFrame object:

```r
r_df <- as.data.frame(py_to_r(df_py$to_dict(as_series = FALSE)), stringsAsFactors = FALSE)
```

This round-trips cleanly (confirmed column types and values match on both sides). Use this pattern in `new_analysis_r.qmd`/`Dashboard_r.qmd` any time Python-side data needs to reach an R chunk (e.g. for `ggplot2`/`dplyr`).

Only `new_analysis.qmd` and `Dashboard.qmd` have R/reticulate variants. `app.py` (Shiny for Python) and `app_streamlit.py` are Python-native web app runtimes with no meaningful "R via reticulate" equivalent — don't attempt to build one; note this to the user if asked.

## Verified against a real Databricks workspace (2026-08-26)

The full pipeline was tested end-to-end against a real SQL Warehouse and a real PAT: `scripts/databricks_setup.py` connected successfully, the VALUES-clause query returned the expected 20 rows with `Days_Waiting` as `Int64` (confirming the `pandera` `coerce=True` fix above was necessary, not speculative), `validate_data.py`/`quality_check.py` passed against the real data, and `new_analysis.qmd`, `Dashboard.qmd`, `new_analysis_r.qmd`, and `Dashboard_r.qmd` all rendered cleanly from it. The bad-host slow-connection-failure gotcha above was found separately, before a real workspace was available, and wasn't re-tested against a real host (no reason to expect a successful connection to behave differently, but it's a fast, successful path, not the slow-failure one — noted for precision). `app.py` was confirmed to import and build its UI correctly against the real cache; the reactive filtering itself was not separately re-verified.
