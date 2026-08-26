# AI driven Analytics with Databricks + Posit

# https://pub.current.posit.team/public/Posit_Databricks_Healthcare_Data_Science/#/title-slide

A workshop demonstrating how to build clinical analytics applications using Databricks as your data warehouse and Posit tools (Positron IDE, Quarto, Shiny, Streamlit) as your development environment.

**Workshop delivery:** AI driven Analytics with Databricks + Posit
**Instructor:** Posit Team & Posit Assistant (AI co-developer in Positron)
**Attendees:** 10-30 clinical analytics & IT staff

---

## Quick Start

### Prerequisites
- [Databricks Free Edition account](https://www.databricks.com/learn/free-edition) or existing workspace access
- [Positron IDE](https://positron.posit.co) installed locally
- Python 3.14+
- (Optional, for the R path) R 4.4+ with the `reticulate` package

### Setup (10-15 minutes)

1. **Fork this repo** and clone locally
2. **Open in Positron:** File → Open Folder → select the cloned repo
3. **Get your Databricks credentials:**
   - Workspace URL (e.g., `dbc-xxxx.cloud.databricks.com`)
   - SQL Warehouse HTTP Path (e.g., `/sql/1.0/warehouses/xxxxxxxx`)
   - Personal Access Token (PAT)
4. **Make sure you have a `.venv`.** If you used File → New Project → Python to create this project, Positron already made one for you. If you opened an existing folder instead, create one now: `python3.14 -m venv .venv`, then set Positron's Python interpreter (top-right) to it — this is what Positron's **Render** button actually uses, separately from `QUARTO_PYTHON` in `.env`. `.env` and the R workflow both assume `.venv` exists — `scripts/check_packages.py` (next step) checks for it and tells you exactly what to do if it's missing.
5. **Create your `.env` file** — ask Posit Assistant:
   > "Create a `.env` file in my project root with fields DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN, and QUARTO_PYTHON=.venv/bin/python. Leave the values blank — I'll fill them in."

   Then open the new `.env` file and type in your real credentials. (If you're comfortable with a terminal, `cp .env.example .env` does the same thing.)
6. **Check your packages:**
   ```bash
   python scripts/check_packages.py
   ```
   This is infrastructure, not a prompting exercise — just run it. It checks everything the workshop needs and installs anything missing, one package at a time, with a specific hint if something fails — including whether `.venv` exists and whether `shiny`/`streamlit`'s commands will actually be found when you run them later.
7. **Materialize the dataset:**
   ```bash
   python scripts/databricks_setup.py
   ```
   Connects to Databricks, runs the workshop's query, and writes `data/waiting_list.parquet`. If this completes cleanly, your `.env` and warehouse are working — every working document below reads from this cache afterward instead of re-querying live each time.

---

## The Four Workflows

Each of these files is **already scaffolded** — section headers/markers are in place, with no placeholder code underneath them. Ask Posit Assistant to fill in each section, one at a time; it inserts a real code block in place when you prompt it.

### Workflow 1: `new_analysis.qmd`
Data exploration and charting, reading from the shared cache.

**Ask Posit Assistant**, at the marker under each header:
> "Using the df DataFrame loaded above, create a Plotly bar chart showing average waiting days by hospital, with a dashed red line at RTT_THRESHOLD (126 days). Use NHS blue (#005EB8) for the bars."

Render with Quarto.

### Workflow 2: `Dashboard.qmd`
KPI dashboard with interactive charts.

**Ask Posit Assistant**, at the marker under each row/column:
> "Add 4 KPI value boxes here — Total Referrals, Average Wait Days, Max Wait, and 18-Week Breaches (>126 days) — using the df DataFrame loaded above."

Render with Quarto.

### Workflow 3: `app.py`
Reactive web app with live filters (Shiny for Python). **The pacing bottleneck of this workshop** — reactive programming (`@reactive.calc`, `@render.ui`) is the first genuinely new programming model, budget extra time here.

**Ask Posit Assistant**, at the marker in each section:
> "Build the sidebar with filters for Priority and Specialty (dropdowns with an 'All' option), and a checkbox group for Hospital Sites."

Run with: `shiny run app.py`

### Workflow 4: `app_streamlit.py`
What-if capacity planner (Streamlit).

**Ask Posit Assistant**, at the marker in each section:
> "Add a sidebar slider to adjust RTT wait targets (14–126 days), then reactive metrics showing breaches at target, delta vs the 126-day baseline, and estimated additional FTE staff needed (formula: breaches × 45 / (7.5 × 60 × 5 × 48))."

Run with: `streamlit run app_streamlit.py`

---

## Choose Your Language: Python or R (via reticulate)

Workflows 1–2 have R-first twins — `new_analysis_r.qmd` and `Dashboard_r.qmd` — that read the same Databricks-backed dataset through `reticulate`, then hand off to `dplyr`/`ggplot2` for analysis. Same backend, either language; a live demo of Positron's polyglot IDE.

These are separate files from the Python versions, not mixed R/Python chunks in one document. Only Workflows 1–2 have this path — Shiny-for-Python and Streamlit are Python-native web runtimes with no meaningful "R via reticulate" equivalent.

Run `Rscript scripts/check_packages.R` first — it checks `reticulate`, `dplyr`, `ggplot2`, and `gt` are installed (falling back to a personal R library if the system one isn't writable), and confirms `.venv` exists before you hit the R documents. See `.posit/assistant/skills/databricks-healthcare-workshop/SKILL.md` for the tested reticulate setup recipe and a couple of non-obvious reticulate/Polars conversion gotchas.

---

## Shared Infrastructure

- `scripts/check_packages.py` — checks/installs pinned package versions, checks Python version, `.venv` existence, and whether `shiny`/`streamlit`'s commands will actually be found on PATH
- `scripts/check_packages.R` — R-side equivalent for the reticulate workflow (`reticulate`, `dplyr`, `ggplot2`, `gt`)
- `scripts/databricks_setup.py` — one-time connection + data materialization into `data/waiting_list.parquet` (`--refresh` to force a live re-query)
- `scripts/databricks_helpers.py` — shared connection/query logic (`load_waiting_list()`, `RTT_THRESHOLD`) used by every working document, so the same ~15-line Databricks boilerplate isn't re-pasted into each file
- `scripts/create_workshop_docs.py` — the deterministic scaffold script that generated `Dashboard.qmd`, `app.py`, `app_streamlit.py` (safe to re-run — skips files that already exist)
- `validation/validate_data.py`, `validation/quality_check.py` — standalone data QA scripts, run directly, not built via prompting

---

## Solutions Folder

All four workflows have ready-to-run solutions in the `solutions/` folder:

```bash
# Quarto examples
quarto render solutions/databricks_clinical_analytics.qmd
quarto render solutions/Dashboard.qmd

# Shiny app
shiny run solutions/app.py

# Streamlit apps
streamlit run solutions/app_streamlit.py
streamlit run solutions/streamlit_app/app.py
```

If anything isn't working, run a solution to see a working example.

---

## Key Files

- `new_analysis.qmd`, `Dashboard.qmd`, `app.py`, `app_streamlit.py` — scaffolded templates for the four workflows (headers/markers in place, no placeholder code)
- `new_analysis_r.qmd`, `Dashboard_r.qmd` — R/reticulate variants of Workflows 1–2
- `scripts/` — infrastructure (package check, dataset setup, shared connection helper, scaffold generator)
- `validation/` — standalone data QA scripts
- `.env.example` — template for credentials (copy to `.env` and fill in your values)
- `.posit/assistant/skills/databricks-healthcare-workshop/SKILL.md` — schema, shared helper usage, and every environment gotcha found while building/testing this workshop
- `solutions/` — fully working examples for all four workflows
- `slides/` — workshop presentation slides

---

## Security Notes

- **Never commit `.env`** — it contains your Databricks Personal Access Token
- `.env` is in `.gitignore` by default
- Always use `.env.example` as your template
- Posit Assistant references credentials via `python-dotenv`, so your token never appears in code or prompts

---

## Architecture

```
┌─────────────────────┐
│   POSITRON IDE      │
│ + Posit Assistant   │
└──────────┬──────────┘
           │ SQL query (once, cached locally after)
           ↓ result set
┌─────────────────────┐
│  DATABRICKS         │
│  SQL Warehouse      │
│  + Healthcare data  │
│  + Unity Catalog    │
└─────────────────────┘
```

Data never leaves Databricks except as the cached result set. Posit queries it live once via `scripts/databricks_setup.py`; every working document reads the local cache afterward.

---

## Next Steps

- 🤖 Ask **Posit Assistant** for any modifications or new analyses
- 📊 Publish your dashboards to Posit Connect
- 🚀 Explore advanced AI features: `chatlas`, `querychat`, `Orbital`

---

## Resources

- [Posit + Databricks](https://posit.co/solutions/databricks)
- [Positron IDE](https://positron.posit.co)
- [Shiny for Python](https://shiny.posit.co/py/)
- [Quarto Dashboards](https://quarto.org/docs/dashboards/)
- [Databricks Unity Catalog](https://www.databricks.com/product/unity-catalog)

---

**Questions?** Ask Posit Assistant in Positron—it knows your Databricks context and can regenerate code, troubleshoot, or help you build something new.
