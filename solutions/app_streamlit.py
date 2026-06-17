import os

from dotenv import load_dotenv

load_dotenv()

import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from databricks import sql

# ── NHS brand colours ─────────────────────────────────────────────────────────
NHS_BLUE   = "#005EB8"
NHS_DARK   = "#003087"
NHS_GREEN  = "#009639"
NHS_AMBER  = "#FFB81C"
NHS_RED    = "#DA291C"
NHS_PURPLE = "#7C2855"

NHS_TARGET = 126  # 18-week standard in days

HOSPITAL_COLOURS = {
    "Glangwili General Hospital": NHS_BLUE,
    "Withybush General Hospital": NHS_DARK,
    "Prince Philip Hospital":     NHS_GREEN,
    "Bronglais General Hospital": NHS_PURPLE,
}

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hywel Dda · Clinical Capacity Planner",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Sidebar ── */
[data-testid="stSidebar"] { background-color: #003087 !important; }
[data-testid="stSidebar"] label  { color: rgba(255,255,255,0.9) !important; font-weight: 600; }
[data-testid="stSidebar"] p      { color: rgba(255,255,255,0.8) !important; }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #ffffff !important; }
[data-testid="stSidebar"] hr     { border-color: rgba(255,255,255,0.2) !important; }
[data-testid="stSidebar"] input  { color: #1a1a1a !important; background: #ffffff !important; }
[data-testid="stSidebar"] button { background: #005EB8 !important; color: #ffffff !important;
                                   border: none !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)


# ── Data — open/close connection inside cached fn (no shared state) ───────────
@st.cache_data(ttl=600, show_spinner="Querying Databricks SQL Warehouse…")
def load_data() -> pl.DataFrame:
    conn = sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"],
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DATABRICKS_TOKEN"],
    )
    query = """
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
    with conn.cursor() as cur:
        cur.execute(query)
        df = pl.DataFrame(
            cur.fetchall(),
            schema=["Hospital", "Specialty", "Days_Waiting", "Priority", "Pathway"],
            orient="row",
        )
    conn.close()
    return df


# ── Load data with explicit error handling ────────────────────────────────────
try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to load data from Databricks: {e}")
    st.stop()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 NHS Wales")
    st.markdown("Clinical Capacity Planner")
    st.divider()

    st.markdown("### 🎯 What-If Target")
    target = st.slider(
        "Maximum Wait Target (Days)",
        min_value=14, max_value=NHS_TARGET, value=NHS_TARGET, step=7,
        help="Drag left to simulate a tighter wait target. NHS standard = 126 days (18 weeks).",
    )
    st.markdown(f"≈ **{round(target / 7, 1)} weeks**")
    st.divider()

    appt_mins = st.number_input(
        "Avg appointment (minutes)", min_value=15, max_value=120, value=45, step=15,
    )
    st.divider()

    if st.button("↻ Refresh from Databricks", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("⚡ Live · Databricks SQL Warehouse")


# ── Calculations ──────────────────────────────────────────────────────────────
nhs_breaches    = df.filter(pl.col("Days_Waiting") > NHS_TARGET).height
target_breaches = df.filter(pl.col("Days_Waiting") > target).height
delta_breaches  = target_breaches - nhs_breaches
working_mins    = 7.5 * 60 * 5 * 48
extra_fte       = round((delta_breaches * appt_mins) / working_mins, 2)


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(f"## 🏥 Clinical Capacity Planner")
st.markdown("**NHS Wales Health Board** · Referral-to-Treatment What-If Analysis")
st.divider()


# ── KPI metrics ───────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Patients",              df.height)
k2.metric("NHS 18-Wk Breaches",          nhs_breaches)
k3.metric(
    f"Breaches at {target}-Day Target",
    target_breaches,
    delta=f"+{delta_breaches} vs NHS standard" if delta_breaches > 0 else "Same as NHS standard",
    delta_color="inverse",
)
k4.metric("Est. Additional FTE", f"{extra_fte}",
          help=f"Based on {appt_mins}-min appointments, 7.5hr days, 48-week year")


# ── What-if callout ───────────────────────────────────────────────────────────
if delta_breaches > 0:
    st.warning(
        f"⚠️ Moving from the NHS 18-week standard (126 days) to a **{target}-day** target "
        f"creates **{delta_breaches} additional breaches** across Hywel Dda sites, "
        f"requiring approximately **{extra_fte} additional clinical FTE** to meet demand."
    )
elif target == NHS_TARGET:
    st.info(
        f"ℹ️ Currently tracking against the NHS 18-week (126-day) standard. "
        f"**{nhs_breaches} patients** are breaching this target."
    )
else:
    st.success("✅ No additional breaches at this target. All patients are within the threshold.")

st.divider()


# ── Charts ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("**📊 Breach Count by Hospital at Selected Target**")
    df_breach = (
        df.with_columns(
            pl.when(pl.col("Days_Waiting") > target)
            .then(pl.lit("Breach"))
            .otherwise(pl.lit("Within Target"))
            .alias("Status")
        )
        .group_by(["Hospital", "Status"])
        .agg(pl.len().alias("Count"))
        .sort("Hospital")
    )
    fig_bar = px.bar(
        df_breach, x="Hospital", y="Count", color="Status",
        color_discrete_map={"Breach": NHS_RED, "Within Target": NHS_GREEN},
        barmode="stack",
        labels={"Count": "Patients", "Hospital": ""},
    )
    fig_bar.update_layout(
        plot_bgcolor="white", height=320,
        margin=dict(l=10, r=10, t=10, b=80),
        xaxis_tickangle=-20,
        legend=dict(orientation="h", yanchor="top", y=-0.35),
        yaxis=dict(showgrid=True, gridcolor="#eee"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.markdown("**📈 Patient Wait Times vs Target**")
    df_scatter = df.with_columns(
        pl.when(pl.col("Days_Waiting") > target)
        .then(pl.lit("Breach"))
        .otherwise(pl.lit("Within Target"))
        .alias("Status")
    )
    fig_strip = px.strip(
        df_scatter, x="Hospital", y="Days_Waiting",
        color="Status",
        color_discrete_map={"Breach": NHS_RED, "Within Target": NHS_GREEN},
        hover_data=["Specialty", "Priority"],
        labels={"Days_Waiting": "Days Waiting", "Hospital": ""},
    )
    fig_strip.add_hline(
        y=target, line_dash="dash", line_color=NHS_BLUE,
        annotation_text=f"Target: {target} days",
        annotation_position="top right",
        annotation_font_color=NHS_BLUE,
    )
    fig_strip.update_layout(
        plot_bgcolor="white", height=320,
        margin=dict(l=10, r=10, t=10, b=80),
        xaxis_tickangle=-20,
        legend=dict(orientation="h", yanchor="top", y=-0.35),
        yaxis=dict(showgrid=True, gridcolor="#eee"),
    )
    st.plotly_chart(fig_strip, use_container_width=True)


# ── Roster table ──────────────────────────────────────────────────────────────
st.markdown("**📋 Full Patient Roster — Breach Status at Selected Target**")

df_display = (
    df.with_columns(
        pl.when(pl.col("Days_Waiting") > NHS_TARGET)
        .then(pl.lit("⚠️ NHS Breach"))
        .when(pl.col("Days_Waiting") > target)
        .then(pl.lit("🟡 Target Breach"))
        .otherwise(pl.lit("✅ Within Target"))
        .alias("Status")
    )
    .sort("Days_Waiting", descending=True)
)

def colour_row(row):
    if "NHS Breach" in str(row.get("Status", "")):
        c = "#ffd5d5"
    elif "Target Breach" in str(row.get("Status", "")):
        c = "#fff3cd"
    else:
        c = "#f0fff4"
    return [f"background-color: {c}"] * len(row)

st.dataframe(
    df_display.to_pandas().style.apply(colour_row, axis=1),
    use_container_width=True,
    height=460,
)
