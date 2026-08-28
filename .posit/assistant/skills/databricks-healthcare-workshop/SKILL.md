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

## `.venv` is assumed by three separate things — check it exists, don't assume

Tested finding (real student dry run, no `.venv` created): `QUARTO_PYTHON=.venv/bin/python` in `.env`, and the hardcoded `use_python(getwd()/.venv/bin/python)` call in both `new_analysis_r.qmd` and `Dashboard_r.qmd`, all silently assume `.venv` exists. If a student opens this folder directly instead of using Positron's File > New Project > Python (which creates `.venv` automatically), all three break with unrelated-looking errors. `scripts/check_packages.py` and `scripts/check_packages.R` now both check for `.venv/bin/python` explicitly and print a clear fix rather than letting this surface downstream. The R docs now also `stop()` with a clear message instead of reticulate's raw error if it's missing.

**Confirmed separately: `.env`'s `QUARTO_PYTHON` does not control Positron's own Render button.** Rendering via `quarto render` on the CLI with `QUARTO_PYTHON` exported picks it up correctly, but clicking Render inside Positron uses whatever interpreter is selected top-right, independent of `.env`. If a document fails to render only when using the Render button (not the CLI), check the interpreter selector first — telling someone to "just check `.env`" isn't the fix here.

**Confirmed on a real live workshop: this repo's own instructed flow (fork + clone, open as an existing folder) is exactly the case where Positron's interpreter selector does NOT auto-switch to `.venv`.** The one mitigation this file used to suggest — "use File > New Project > Python, it handles this" — doesn't apply to the flow the workshop actually tells people to use. Two real, tested fixes now in place: (1) a committed `.vscode/settings.json` setting `python.defaultInterpreterPath` to `.venv/bin/python`, intended to pre-select it on folder-open — **not independently verified that Positron's UI actually honors this**, tell the user to visually check the selector regardless; (2) `check_packages.py` prints an explicit reminder to verify the interpreter selector matches `.venv`. Don't assume opening the folder was enough.

**Confirmed real: a machine can be missing the Python 3.14 binary entirely, not just "the wrong version already installed."** `python3.14 -m venv .venv` fails outright with no Python 3.14 anywhere on the system. `uv venv --python 3.14.2 .venv` is the tested fix — `uv` downloads/manages that exact Python version itself if it's missing, and is now the primary documented command (not just a fallback).

**Confirmed real: `uv venv` deliberately creates a venv with no `pip` installed** (by design, not a bug — unlike `python -m venv`, which always includes it). `check_packages.py` now detects this (`import pip` failing) and self-heals via `python -m ensurepip` before attempting any package installs, rather than failing confusingly mid-loop. Tested end-to-end against a genuinely fresh, pip-less `uv venv`.

## Installed CLI commands (`shiny`, `streamlit`) can exist but not be on PATH

Tested finding: checking `shutil.which("streamlit")` against the system PATH is unreliable — a stale, unrelated install elsewhere on PATH can produce a false "ok" that has nothing to do with this project's `.venv`. What matters is whether `.venv/bin` itself is on PATH (i.e., whether the venv is activated) — `scripts/check_packages.py` checks that specifically now. If `.venv/bin` isn't on PATH, a bare `streamlit run app_streamlit.py` may fail or silently run a different install; use `.venv/bin/streamlit run ...` or `source .venv/bin/activate` first.

## R side has no package-check infrastructure of its own — now fixed

Tested finding: nothing checked whether `reticulate` (or `dplyr`/`ggplot2`/`gt`) were installed before a student hit `new_analysis_r.qmd`/`Dashboard_r.qmd` — only `check_packages.py` (Python) existed. `scripts/check_packages.R` now covers this, including falling back to a user library (`R_LIBS_USER`) if the system R library isn't writable (the same "no sudo" problem `check_packages.py` sidesteps via pip's own fallback, made explicit here).

## `shinywidgets` is required for Workflow 3's interactive Plotly-in-Shiny

Tested finding: prompting Assistant for interactive Plotly charts inside `app.py` (Workflow 3) produces code depending on `shinywidgets` (`render_plotly`/`render_widget`), which wasn't in `check_packages.py`'s list — a student following the scripted prompts hit `ModuleNotFoundError` with nothing catching it first. Now included (`shinywidgets==0.8.1`).

## Multiple Python interpreters can be in play at once

This machine (and possibly a student's) can have several Python interpreters — the one Positron's console uses, the one a bare `python3` in a terminal resolves to, and `.venv`'s. They aren't guaranteed to be the same. "I ran `check_packages.py` and it passed" only guarantees packages are installed for *that* interpreter. If something imports fine in one place but not another, check `sys.executable` in both rather than assuming the package check was wrong.

Confirmed the same is true for R: the console's `.libPaths()` can differ from what `Rscript`/bash used, so a package installed via `scripts/check_packages.R` from a terminal may still show `FALSE` for `requireNamespace()` in the actual console until that console's `.libPaths()` includes the same library. Same fix as Python: check where the *actual* console is looking, don't assume a passing script means the visible session has it too.

**After switching Positron's interpreter (or restarting a kernel), the very first `sys.executable`/import check can lag/appear stale for a moment.** If a check right after a switch still shows the old interpreter, re-check once before concluding the switch didn't work — don't immediately troubleshoot as if it's still broken.

**Never write code that puts a real credential value directly in a cell, script, or chat message** — always route through `load_waiting_list()`/`databricks_helpers.py`, which reads from `.env` via `os.getenv()`. If asked to "just paste in the token to test it," don't — suggest putting it in `.env` instead, even for a quick one-off test.

## If a package was installed after a console/kernel was already running

Restart the console/kernel before assuming an import failure means something's actually broken. Two real causes of this, tested: (1) a package installed to user site-packages isn't always visible to an already-running interpreter's `sys.path`; (2) Plotly specifically caches "not importable" for optional deps like `nbformat` the first time it checks, and won't re-check after a later install in the same session. Restarting fixes both — don't debug import internals first.

## Plotly rendering — use the pattern this workshop already uses, not `fig.show()`

Every `.qmd`/dashboard document renders a figure by making it the last expression in a cell (Quarto's Jupyter engine displays it automatically) — that's already correct and needs no renderer configuration. Don't suggest `fig.show()` as a fix for "nothing displayed" — its default renderer opens a browser tab, which does nothing useful in a non-interactive or headless context. Static image export (`fig.write_image(...)`) additionally pulls in `kaleido`, which needs a full headless-Chromium install — heavier than it looks; avoid suggesting it unless actually needed.

## Deploying to Posit Connect — two non-interoperable paths

If a document gets deployed (e.g. after the Dashboard step), there are two separate, non-interoperable ways to do it: Positron's Publisher UI ("Publish" button) and the `rsconnect-python` package/CLI. **Ask which one the user wants before starting** — don't assume. If someone already clicked "Publish" and it's incomplete, check for a leftover config file before starting a fresh `rsconnect`-driven deployment from scratch.

**If switching paths after a failed first attempt, don't just start the second path — clean up the first.** Confirmed real (live workshop): switching Publisher → `rsconnect` after a failed Publisher attempt created a *second*, separate app on Connect rather than fixing/replacing the first, leaving two content records. If a first attempt already reached Connect (even partially/broken), find and archive or delete that content record as part of switching paths, not after the fact.

**Publisher's file auto-detection can silently drop files a document actually needs at runtime.** Confirmed real: a Publisher deploy of a document using `sys.path.insert(...)` + `import databricks_helpers` (the pattern every document in this workshop uses to reach `scripts/databricks_helpers.py`) omitted that file and the cached data file from the bundle, and the deployed app crashed on Connect with no local reproduction. Auto-detection apparently doesn't follow this import pattern. If deploying any of the four documents, explicitly verify (or set) the files list in the Publisher config includes `scripts/databricks_helpers.py` and `data/waiting_list.parquet` — don't trust auto-detection for this repo's specific import style. This wasn't independently re-tested against a real Connect server from this session — flag it to the user as something to check rather than asserting the exact config fix, since the correct config schema wasn't verified here either.

**`requirements.txt` exists at the repo root specifically for CLI (`rsconnect`) deploys.** Confirmed real failure mode: with no `requirements.txt` present, `rsconnect deploy` fell back to `pip freeze`, which captured an unrelated system Python's ~194 packages (including a broken sdist) instead of `.venv`'s actual dependencies — nondeterministic, and wrong. `requirements.txt` now pins the same exact versions as `check_packages.py`; keep them in sync if either changes.

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

## Package installs go through Posit Package Manager, not raw PyPI/CRAN

Confirmed by testing, not assumed: `check_packages.py` installs from PPM's Python mirror (`https://p3m.dev/pypi/latest/simple`) — safe at `/latest` since every package is already pinned to an exact version with `==`. `check_packages.R` pins CRAN to a **dated** PPM snapshot (`https://p3m.dev/cran/__linux__/jammy/2026-08-25`) rather than this environment's default `/latest`, since `install.packages()` has no version pin of its own — the snapshot date is what makes an R install reproducible. Don't remove either index/repo setting or fall back to plain PyPI/CRAN — both were verified to work with the full package list on the actual pinned interpreter/R version this workshop targets.

**`polars==1.44.0` was yanked upstream on PyPI** (confirmed via PyPI's own JSON API — reason given: "when/then/otherwise regression"), and this exposed a real gap: PPM's `/latest` mirror kept serving 1.44.0 fine for local installs even after PyPI itself pulled it, while a real Connect deploy (which resolves against actual PyPI) correctly refused it. **"Installs fine locally via PPM" is not proof a pin is safe to deploy.** The pin is now `polars==1.44.1` everywhere (`check_packages.py`, `requirements.txt`) — confirmed this version installs cleanly and the specific regression is fixed. If a Connect deploy ever rejects a version that installs fine locally, check PyPI directly for a yank before assuming it's a config problem on your end.

**Tried to reproduce a reported `plotly.express` + Polars incompatibility (claim: needs manual `.to_pandas()`) and could not**, with the exact pinned versions in this repo (`plotly==7.0.0`, `polars==1.44.1`) — `px.bar`, `px.box` with `color`/`points`/`hover_data` all worked directly against a Polars DataFrame in testing. If this resurfaces, it may be version-specific to a different `plotly`/`polars` combination than what's pinned here — get the exact versions involved before assuming it's still true for this repo's pins.
