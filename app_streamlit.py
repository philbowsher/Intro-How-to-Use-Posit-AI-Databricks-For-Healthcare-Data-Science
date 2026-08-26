"""NHS Wales · Clinical Capacity Planner -- Streamlit what-if app.

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
