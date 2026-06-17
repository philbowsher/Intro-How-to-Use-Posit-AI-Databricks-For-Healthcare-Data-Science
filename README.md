# Meridian Health Trust Clinical Analytics with Databricks + Posit

# https://pub.current.posit.team/public/Posit_Databricks_Healthcare_Data_Science/#/title-slide

A workshop demonstrating how to build clinical analytics applications using Databricks as your data warehouse and Posit tools (Positron IDE, Quarto, Shiny, Streamlit) as your development environment.

**Workshop delivery:** Meridian Health Trust  
**Instructor:** Posit Assistant (AI co-developer in Positron)  
**Attendees:** 30 clinical analytics & IT staff

---

## Quick Start

### Prerequisites
- [Databricks Free Edition account](https://www.databricks.com/learn/free-edition) or existing workspace access
- [Positron IDE](https://positron.posit.co) installed locally
- Python 3.10+

### Setup (5 minutes)

1. **Fork this repo** and clone locally
2. **Open in Positron:** File → Open Folder → select the cloned repo
3. **Get your Databricks credentials:**
   - Workspace URL (e.g., `dbc-xxxx.cloud.databricks.com`)
   - SQL Warehouse HTTP Path (e.g., `/sql/1.0/warehouses/xxxxxxxx`)
   - Personal Access Token (PAT)

4. **Create your `.env` file:**
   ```bash
   cp .env.example .env
   ```
   Then fill in your Databricks credentials in `.env`

5. **Ask Posit Assistant to install packages:**
   - Open Posit Assistant (bottom-left chat icon in Positron)
   - Tell it: "Install these packages via pip: databricks-sql-connector, polars, plotly, shiny, streamlit, python-dotenv, nbformat, nbclient, nbconvert, ipykernel"
   - Run the pip command in Positron's terminal

---

## The Four Workflows

### Workflow 1: `new_analysis.qmd`
Data import, connection verification, and exploration.

**Ask Posit Assistant:**
> "Fill in new_analysis.qmd: (1) use python-dotenv to load DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN from my .env file, (2) connect to Databricks, (3) execute a VALUES query with hospital, specialty, days_waiting, priority, (4) convert to Polars DataFrame `df`. Then add average waiting days by specialty and a Plotly bar chart with professional blue bars and a red dashed line at 126 days."

Render with Quarto.

### Workflow 2: `Dashboard.qmd`
KPI dashboard with interactive charts.

**Ask Posit Assistant:**
> "Create a new file Dashboard.qmd with Quarto dashboard format. Include: (1) 4 KPI value boxes (Total Referrals, Average Wait Days, Max Wait, 18-Week Breaches >126 days), (2) interactive Plotly bar chart by specialty, (3) box plot by priority level. Use professional blue for colours. Use the same Databricks connection setup as new_analysis.qmd."

Render with Quarto.

### Workflow 3: `app.py`
Reactive web app with live filters (Shiny for Python).

**Ask Posit Assistant:**
> "Create a new file app.py. Build a Shiny for Python app with: (1) sidebar filters for Priority and Specialty, (2) 4 reactive KPI value boxes that update when filters change, (3) 3 interactive Plotly charts that filter reactively. Use the same Databricks connection setup as new_analysis.qmd."

Run with: `shiny run app.py`

### Workflow 4: `app_streamlit.py`
What-if capacity planner (Streamlit).

**Ask Posit Assistant:**
> "Create a new file app_streamlit.py. Build a Streamlit app with: (1) sidebar slider to adjust RTT wait targets (14–126 days), (2) reactive metrics showing breaches at target, delta vs 126-day baseline, and estimated additional FTE staff needed (formula: breaches × 45 / (7.5 × 60 × 5 × 48)), (3) update all metrics and charts as the slider moves. Use the same Databricks connection setup as new_analysis.qmd."

Run with: `streamlit run app_streamlit.py`

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

- `new_analysis.qmd` — Blank template for Workflow 1 (attendees fill in with Posit Assistant help)
- `Dashboard.qmd` — Blank template for Workflow 2
- `app.py` — Blank template for Workflow 3
- `app_streamlit.py` — Blank template for Workflow 4
- `.env.example` — Template for credentials (copy to `.env` and fill in your values)
- `solutions/` — Fully working examples for all four workflows
- `slides/` — Workshop presentation slides

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
           │ SQL query
           ↓ result set
┌─────────────────────┐
│  DATABRICKS         │
│  SQL Warehouse      │
│  + Healthcare data  │
│  + Unity Catalog    │
└─────────────────────┘
```

Data never leaves Databricks. Posit queries it live and brings back only the result set.

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
