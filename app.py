"""NHS Wales · Clinical Access & Performance -- Shiny for Python app.

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
# (dropdowns, with an 'All' option), and a checkbox group for Hospital Sites."
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
