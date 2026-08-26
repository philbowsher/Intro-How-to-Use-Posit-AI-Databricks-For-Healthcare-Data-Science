"""Run this once to scaffold the workshop's working documents with section
headers/markers already in place. This is deterministic setup, not a
prompting exercise -- just run it.

Safe to re-run: it will not overwrite a file that already exists.

Run it with:  python scripts/create_workshop_docs.py

Lesson carried over from an earlier workshop iteration (tested the hard
way): scaffolded sections are markdown headers or comment markers ONLY --
never a pre-filled or "placeholder" code chunk/stub. Two things were tried
and found confusing: (1) `# PROMPT: ...` comments inside an otherwise
runnable chunk, and (2) locator comments standing in for real code. Both
made it unclear what was real vs. what Assistant was supposed to replace.
What works: a bare header/marker with nothing under it -- Posit Assistant
inserts a real chunk live, in place, when the student prompts it for that
section. The one exception is genuine shared infrastructure (the
self-loading data import at the top of each file) -- that's real working
code, not a placeholder, so it stays.

new_analysis.qmd is not regenerated here -- it already exists as a
hand-built template with this same self-loading-data pattern.
"""

from pathlib import Path

DASHBOARD_QMD = '''---
title: "NHS Wales · Clinical Access & Performance"
subtitle: "Referral-to-Treatment Intelligence Dashboard"
author: "Clinical Intelligence Unit"
date: today
format:
  dashboard:
    orientation: rows
    theme: cosmo
    scrolling: true
execute:
  echo: false
  warning: false
---

<!-- Ask Posit Assistant to write the code for each row below, then run the chunk it inserts. -->
<!-- This setup chunk makes the document self-contained: it loads the waiting-list data even if -->
<!-- you open this file fresh, without needing to re-run scripts/databricks_setup.py first. -->

```{python}
#| label: setup
#| output: false

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "scripts"))

from databricks_helpers import load_waiting_list, RTT_THRESHOLD

df = load_waiting_list()
```

## Row {height="150px"}

<!-- Ask Posit Assistant: "Add 4 KPI value boxes here -- Total Referrals, Average Wait Days,
     Max Wait, and 18-Week Breaches (>126 days) -- using the df DataFrame loaded above." -->

## Row {height="420px"}

### Column {width=58%}

<!-- Ask Posit Assistant: "Add a Plotly horizontal bar chart of average waiting days by
     hospital, with a dashed red line at the 126-day RTT_THRESHOLD." -->

### Column {width=42%}

<!-- Ask Posit Assistant: "Add a Plotly donut chart of referral counts by priority level." -->

## Row {height="420px"}

### Column {width=55%}

<!-- Ask Posit Assistant: "Add a Plotly box plot of wait times by specialty, with a dashed
     red line at RTT_THRESHOLD." -->

### Column {width=45%}

<!-- Ask Posit Assistant: "Add a Plotly table of the full waiting list, colour-coding rows
     that breach RTT_THRESHOLD." -->
'''

APP_PY = '''"""NHS Wales · Clinical Access & Performance -- Shiny for Python app.

Scaffolded by scripts/create_workshop_docs.py. Ask Posit Assistant to fill
in each section marked below, one at a time -- select the file, press
Cmd/Ctrl+I, describe what you need for that section.

Run with: shiny run app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from databricks_helpers import load_waiting_list, RTT_THRESHOLD
from shiny import App, reactive, render, ui

BASE_DATA = load_waiting_list()

HOSPITALS = sorted(BASE_DATA["Hospital"].unique().to_list())
PRIORITIES = sorted(BASE_DATA["Priority"].unique().to_list())
SPECIALTIES = sorted(BASE_DATA["Specialty"].unique().to_list())


# Ask Posit Assistant: "Build the sidebar with filters for Priority and Specialty
# (dropdowns, with an \\'All\\' option), and a checkbox group for Hospital Sites."
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.markdown("_Filters go here -- ask Posit Assistant to build this sidebar._"),
    ),

    # Ask Posit Assistant: "Add 4 reactive KPI value boxes: Total Referrals,
    # Average Wait, Longest Wait, 18-Week Breaches -- that update when filters change."

    # Ask Posit Assistant: "Add 3 interactive Plotly charts that filter reactively:
    # a bar chart of average wait by hospital, a donut chart of referrals by priority,
    # and a box plot of wait distribution by specialty. Use RTT_THRESHOLD (126 days)
    # as a reference line where relevant."

    title="NHS Wales · Clinical Access & Performance",
    fillable=True,
)


def server(input, output, session):
    # Ask Posit Assistant: "Add a reactive.calc that filters BASE_DATA by the
    # sidebar inputs, then wire the KPI and chart outputs above to it."
    pass


app = App(app_ui, server)
'''

APP_STREAMLIT_PY = '''"""NHS Wales · Clinical Capacity Planner -- Streamlit what-if app.

Scaffolded by scripts/create_workshop_docs.py. Ask Posit Assistant to fill
in each section marked below, one at a time -- select the file, press
Cmd/Ctrl+I, describe what you need for that section.

Run with: streamlit run app_streamlit.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scripts"))

import streamlit as st
from databricks_helpers import load_waiting_list, RTT_THRESHOLD

st.set_page_config(
    page_title="NHS Wales · Clinical Capacity Planner",
    page_icon="🏥",
    layout="wide",
)

try:
    df = load_waiting_list()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

st.markdown("## 🏥 Clinical Capacity Planner")
st.markdown("**NHS Wales Health Board** · Referral-to-Treatment What-If Analysis")
st.divider()

# Ask Posit Assistant: "Add a sidebar slider to adjust the RTT wait target,
# from 14 to 126 days, defaulting to 126 (the NHS 18-week standard)."

# Ask Posit Assistant: "Add reactive metrics showing: breaches at the selected
# target, the delta vs the 126-day baseline, and estimated additional FTE
# staff needed using: breaches * 45 / (7.5 * 60 * 5 * 48)."

# Ask Posit Assistant: "Add charts and a roster table that update as the
# slider moves -- e.g. a stacked bar of breach status by hospital, and a
# strip plot of wait times vs the selected target."
'''

DOCS = {
    "Dashboard.qmd": DASHBOARD_QMD,
    "app.py": APP_PY,
    "app_streamlit.py": APP_STREAMLIT_PY,
}


def main() -> None:
    for filename, content in DOCS.items():
        path = Path(filename)
        if path.exists():
            print(f"[skip]    {filename} already exists -- not overwriting")
            continue
        path.write_text(content)
        print(f"[created] {filename}")

    print("\nDone. Open each file in Positron and work through it section by section with Posit Assistant.")


if __name__ == "__main__":
    main()
