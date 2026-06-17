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

RTT_THRESHOLD = 126

HOSPITAL_COLOURS = {
    "Glangwili General Hospital": NHS_BLUE,
    "Withybush General Hospital": NHS_DARK,
    "Prince Philip Hospital":     NHS_GREEN,
    "Bronglais General Hospital": NHS_PURPLE,
}
PRIORITY_COLOURS = {
    "2-Week Wait": NHS_RED,
    "Urgent":      NHS_AMBER,
    "Routine":     NHS_BLUE,
}
HOSPITALS   = list(HOSPITAL_COLOURS.keys())
PRIORITIES  = ["All", "Urgent", "Routine", "2-Week Wait"]
SPECIALTIES = ["All", "Cardiology", "Orthopaedics", "Urology", "Dermatology", "Oncology"]


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NHS Wales · Clinical Access & Performance",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #003087;
}
[data-testid="stSidebar"] * {
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label {
    color: rgba(255,255,255,0.85) !important;
    font-weight: 600;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.2);
}

/* Header bar */
[data-testid="stHeader"] {
    background-color: #005EB8;
}

/* Metric cards */
[data-testid="stMetric"] {
    background-color: #ffffff;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-left: 5px solid #005EB8;
}
[data-testid="stMetricLabel"]  { font-weight: 600; color: #003087 !important; }
[data-testid="stMetricValue"]  { color: #005EB8 !important; font-size: 2rem !important; }

/* Chart containers */
[data-testid="stPlotlyChart"] > div {
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    background: white;
    padding: 4px;
}

/* Divider */
hr { border-color: rgba(0,0,0,0.08); }
</style>
""", unsafe_allow_html=True)


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Connecting to Databricks SQL Warehouse…")
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


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 NHS Wales")
    st.markdown(
        "<p style='color:rgba(255,255,255,0.6); font-size:13px; margin-top:-10px;'>"
        "Clinical Intelligence Unit</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    priority  = st.selectbox("Priority Level", PRIORITIES)
    specialty = st.selectbox("Specialty", SPECIALTIES)
    hospitals = st.multiselect(
        "Hospital Sites",
        options=HOSPITALS,
        default=HOSPITALS,
    )

    st.divider()
    if st.button("↻ Refresh from Databricks", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        "<p style='color:rgba(255,255,255,0.45); font-size:11px; margin-top:8px;'>"
        "⚡ Live · Databricks SQL Warehouse</p>",
        unsafe_allow_html=True,
    )


# ── Load & filter data ────────────────────────────────────────────────────────
base_df = load_data()

df = base_df
if priority != "All":
    df = df.filter(pl.col("Priority") == priority)
if specialty != "All":
    df = df.filter(pl.col("Specialty") == specialty)
if hospitals:
    df = df.filter(pl.col("Hospital").is_in(hospitals))


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    f"<h2 style='color:{NHS_DARK}; margin-bottom:0;'>"
    "NHS Wales · Clinical Access & Performance</h2>"
    f"<p style='color:#666; margin-top:4px;'>Referral-to-Treatment Intelligence Dashboard</p>",
    unsafe_allow_html=True,
)
st.divider()


# ── KPI metrics ───────────────────────────────────────────────────────────────
if df.is_empty():
    st.warning("No data matches the selected filters.")
    st.stop()

total    = df.height
avg_wait = round(df["Days_Waiting"].mean(), 1)
max_wait = df["Days_Waiting"].max()
breaches = df.filter(pl.col("Days_Waiting") > RTT_THRESHOLD).height
breach_pct = round(breaches / total * 100, 1)

k1, k2, k3, k4 = st.columns(4)
k1.metric("🧑‍🤝‍🧑 Total Referrals",  total)
k2.metric("🕐 Average Wait",        f"{avg_wait} days")
k3.metric("⚠️ Longest Wait",        f"{max_wait} days")
k4.metric("🛡️ 18-Week Breaches",   f"{breaches} ({breach_pct}%)")

st.divider()


# ── Charts row 1 ──────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**📊 Average Wait by Hospital Site**")
    df_hosp = (
        df.group_by("Hospital")
        .agg(pl.col("Days_Waiting").mean().round(1).alias("Avg"))
        .sort("Avg", descending=True)
    )
    fig_bar = px.bar(
        df_hosp, x="Avg", y="Hospital", orientation="h",
        color="Hospital", color_discrete_map=HOSPITAL_COLOURS,
        text="Avg", labels={"Avg": "Avg Days Waiting", "Hospital": ""},
    )
    fig_bar.add_vline(
        x=RTT_THRESHOLD, line_dash="dash", line_color=NHS_RED,
        annotation_text="18-wk target",
        annotation_position="top right",
        annotation_font_color=NHS_RED,
    )
    fig_bar.update_traces(texttemplate="%{text} days", textposition="outside")
    fig_bar.update_layout(
        showlegend=False, plot_bgcolor="white",
        margin=dict(l=10, r=90, t=10, b=10), height=300,
        xaxis=dict(showgrid=True, gridcolor="#eee"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.markdown(f"**🍩 Referrals by Priority Level**")
    df_pri = df.group_by("Priority").agg(pl.len().alias("Count"))
    fig_pie = px.pie(
        df_pri, names="Priority", values="Count", hole=0.55,
        color="Priority", color_discrete_map=PRIORITY_COLOURS,
    )
    fig_pie.update_traces(textinfo="percent+label", textfont_size=13, pull=0.03)
    fig_pie.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.18),
        margin=dict(l=10, r=10, t=10, b=40),
        height=300,
        annotations=[dict(
            text=f"<b>{total}</b><br>Patients",
            x=0.5, y=0.5, font_size=16, showarrow=False,
        )],
    )
    st.plotly_chart(fig_pie, use_container_width=True)


# ── Charts row 2 ──────────────────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown("**📈 Wait Distribution by Specialty**")
    fig_box = px.box(
        df, x="Specialty", y="Days_Waiting",
        color="Specialty", points="all",
        hover_data=["Hospital", "Priority"],
        labels={"Days_Waiting": "Days Waiting", "Specialty": ""},
        color_discrete_sequence=[NHS_BLUE, NHS_DARK, NHS_GREEN, NHS_AMBER, NHS_PURPLE],
    )
    fig_box.add_hline(
        y=RTT_THRESHOLD, line_dash="dash", line_color=NHS_RED,
        annotation_text="18-wk target",
        annotation_position="top right",
        annotation_font_color=NHS_RED,
    )
    fig_box.update_layout(
        showlegend=False, plot_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10), height=300,
        yaxis=dict(showgrid=True, gridcolor="#eee"),
    )
    st.plotly_chart(fig_box, use_container_width=True)

with col4:
    st.markdown("**📋 Waiting List Roster**")

    def row_colour(days: int) -> str:
        if days > RTT_THRESHOLD:
            return NHS_RED
        if days > 84:
            return NHS_AMBER
        return "#ffffff"

    colours = [row_colour(d) for d in df["Days_Waiting"].to_list()]
    fig_tbl = go.Figure(go.Table(
        header=dict(
            values=["<b>Hospital</b>", "<b>Specialty</b>",
                    "<b>Days</b>", "<b>Priority</b>", "<b>Pathway</b>"],
            fill_color=NHS_BLUE,
            font=dict(color="white", size=12),
            align="left", height=32,
        ),
        cells=dict(
            values=[
                df["Hospital"].to_list(),
                df["Specialty"].to_list(),
                df["Days_Waiting"].to_list(),
                df["Priority"].to_list(),
                df["Pathway"].to_list(),
            ],
            fill_color=[colours],
            font=dict(size=11),
            align="left", height=26,
        ),
    ))
    fig_tbl.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
    st.plotly_chart(fig_tbl, use_container_width=True)
