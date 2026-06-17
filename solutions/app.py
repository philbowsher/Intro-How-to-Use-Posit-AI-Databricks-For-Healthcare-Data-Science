import os

from dotenv import load_dotenv

load_dotenv()

import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from databricks import sql
from shiny import App, reactive, render, ui

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
PRIORITIES  = ["Urgent", "Routine", "2-Week Wait"]
SPECIALTIES = ["Cardiology", "Orthopaedics", "Urology", "Dermatology", "Oncology"]


# ── Load from Databricks once at startup ─────────────────────────────────────
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


BASE_DATA = load_data()


# ── Helpers ───────────────────────────────────────────────────────────────────
def plotly_html(fig: go.Figure) -> ui.HTML:
    return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn"))


def empty_state(msg: str = "No data for selected filters.") -> ui.Tag:
    return ui.div(
        ui.tags.i(class_="bi bi-bar-chart-line", style="font-size:3rem; color:#ccc;"),
        ui.p(msg, style="color:#999; margin-top:8px;"),
        style=(
            "display:flex; flex-direction:column; align-items:center;"
            " justify-content:center; height:250px;"
        ),
    )


# ── Styles ────────────────────────────────────────────────────────────────────
custom_css = """
body { background:#f0f4f5; font-family:Arial,Helvetica,sans-serif; }

/* Sidebar */
.bslib-sidebar-layout > .sidebar { background-color:#003087 !important; }
.sidebar .sidebar-title,
.sidebar label,
.sidebar .control-label { color:#ffffff !important; }
.sidebar .form-select   { border-color:rgba(255,255,255,0.35); }
.sidebar hr             { border-color:rgba(255,255,255,0.25); }
.sidebar-footer         { color:rgba(255,255,255,0.55); font-size:11px; }

/* Cards */
.card        { border:none; box-shadow:0 2px 8px rgba(0,0,0,0.08); border-radius:8px; }
.card-header { background:#fff; font-weight:600; color:#003087;
               border-bottom:2px solid #005EB8; letter-spacing:0.02em; }

/* Value boxes */
.bslib-value-box .value-box-value { font-size:2rem; font-weight:700; }

/* Navbar */
.navbar-brand { color:#ffffff !important; font-weight:700; }
"""

# ── UI ────────────────────────────────────────────────────────────────────────
app_ui = ui.page_sidebar(
    # ── Sidebar (first positional arg) ────────────────────────────────────────
    ui.sidebar(
        ui.div(
            ui.tags.span("🏥", style="font-size:1.4rem;"),
            ui.div(
                ui.tags.strong("NHS Wales",
                               style="color:white; font-size:0.95rem; display:block;"),
                ui.tags.span("Clinical Intelligence Unit",
                             style="color:rgba(255,255,255,0.65); font-size:0.75rem;"),
            ),
            style="display:flex; align-items:center; gap:10px; margin-bottom:18px;",
        ),
        ui.input_select(
            "priority", "Priority Level",
            choices={"All": "All", **{p: p for p in PRIORITIES}},
        ),
        ui.input_select(
            "specialty", "Specialty",
            choices={"All": "All", **{s: s for s in SPECIALTIES}},
        ),
        ui.input_checkbox_group(
            "hospitals", "Hospital Sites",
            choices={h: h for h in HOSPITALS},
            selected=HOSPITALS,
        ),
        ui.hr(),
        ui.div(
            ui.tags.i(class_="bi bi-database-fill-check",
                      style="color:#7aabff; margin-right:4px;"),
            ui.tags.span("Live · Databricks SQL Warehouse",
                         style="color:rgba(255,255,255,0.65); font-size:11px;"),
            class_="sidebar-footer",
        ),
        width=290,
    ),

    # ── CSS ───────────────────────────────────────────────────────────────────
    ui.tags.style(custom_css),

    # ── KPI value boxes ───────────────────────────────────────────────────────
    ui.layout_column_wrap(
        ui.value_box(
            "Total Referrals",
            ui.output_text("kpi_total"),
            showcase=ui.HTML('<i class="bi bi-people-fill" style="font-size:2rem"></i>'),
            theme="primary",
        ),
        ui.value_box(
            "Average Wait",
            ui.output_text("kpi_avg"),
            showcase=ui.HTML('<i class="bi bi-clock-history" style="font-size:2rem"></i>'),
            theme="info",
        ),
        ui.value_box(
            "Longest Wait",
            ui.output_text("kpi_max"),
            showcase=ui.HTML('<i class="bi bi-exclamation-circle-fill" style="font-size:2rem"></i>'),
            theme="warning",
        ),
        ui.value_box(
            "18-Wk Breaches",
            ui.output_text("kpi_breach"),
            showcase=ui.HTML('<i class="bi bi-shield-exclamation" style="font-size:2rem"></i>'),
            theme="danger",
        ),
        fill=False,
        width=1/4,
    ),

    # ── Charts row 1 ──────────────────────────────────────────────────────────
    ui.layout_column_wrap(
        ui.card(
            ui.card_header(
                ui.tags.i(class_="bi bi-bar-chart-fill",
                          style=f"color:{NHS_BLUE}; margin-right:6px;"),
                "Average Wait by Hospital Site",
            ),
            ui.output_ui("chart_hospital"),
            full_screen=True,
        ),
        ui.card(
            ui.card_header(
                ui.tags.i(class_="bi bi-pie-chart-fill",
                          style=f"color:{NHS_PURPLE}; margin-right:6px;"),
                "Referrals by Priority Level",
            ),
            ui.output_ui("chart_priority"),
            full_screen=True,
        ),
        width=1/2,
    ),

    # ── Charts row 2 ──────────────────────────────────────────────────────────
    ui.layout_column_wrap(
        ui.card(
            ui.card_header(
                ui.tags.i(class_="bi bi-activity",
                          style=f"color:{NHS_GREEN}; margin-right:6px;"),
                "Wait Distribution by Specialty",
            ),
            ui.output_ui("chart_specialty"),
            full_screen=True,
        ),
        ui.card(
            ui.card_header(
                ui.tags.i(class_="bi bi-table",
                          style=f"color:{NHS_DARK}; margin-right:6px;"),
                "Waiting List Roster",
            ),
            ui.output_ui("chart_table"),
            full_screen=True,
        ),
        width=1/2,
    ),

    title="NHS Wales · Clinical Access & Performance",
    fillable=True,
)


# ── Server ────────────────────────────────────────────────────────────────────
def server(input, output, session):

    @reactive.calc
    def filtered() -> pl.DataFrame:
        df = BASE_DATA
        if input.priority() != "All":
            df = df.filter(pl.col("Priority") == input.priority())
        if input.specialty() != "All":
            df = df.filter(pl.col("Specialty") == input.specialty())
        selected = list(input.hospitals())
        if selected:
            df = df.filter(pl.col("Hospital").is_in(selected))
        return df

    # ── KPIs ──────────────────────────────────────────────────────────────────
    @render.text
    def kpi_total():
        return str(filtered().height)

    @render.text
    def kpi_avg():
        df = filtered()
        return "—" if df.is_empty() else f"{df['Days_Waiting'].mean():.1f} days"

    @render.text
    def kpi_max():
        df = filtered()
        return "—" if df.is_empty() else f"{df['Days_Waiting'].max()} days"

    @render.text
    def kpi_breach():
        df = filtered()
        if df.is_empty():
            return "0 (0%)"
        n = df.filter(pl.col("Days_Waiting") > RTT_THRESHOLD).height
        pct = n / df.height * 100
        return f"{n} ({pct:.1f}%)"

    # ── Hospital bar chart ────────────────────────────────────────────────────
    @render.ui
    def chart_hospital():
        df = filtered()
        if df.is_empty():
            return empty_state()
        df_h = (
            df.group_by("Hospital")
            .agg(pl.col("Days_Waiting").mean().round(1).alias("Avg"))
            .sort("Avg", descending=True)
        )
        fig = px.bar(
            df_h, x="Avg", y="Hospital", orientation="h",
            color="Hospital", color_discrete_map=HOSPITAL_COLOURS,
            text="Avg", labels={"Avg": "Avg Days Waiting", "Hospital": ""},
        )
        fig.add_vline(
            x=RTT_THRESHOLD, line_dash="dash", line_color=NHS_RED,
            annotation_text="18-wk target",
            annotation_position="top right",
            annotation_font_color=NHS_RED,
        )
        fig.update_traces(texttemplate="%{text} days", textposition="outside")
        fig.update_layout(
            showlegend=False, plot_bgcolor="white",
            margin=dict(l=10, r=90, t=10, b=10), height=280,
            xaxis=dict(showgrid=True, gridcolor="#eee"),
        )
        return plotly_html(fig)

    # ── Priority donut ────────────────────────────────────────────────────────
    @render.ui
    def chart_priority():
        df = filtered()
        if df.is_empty():
            return empty_state()
        df_p = df.group_by("Priority").agg(pl.len().alias("Count"))
        fig = px.pie(
            df_p, names="Priority", values="Count", hole=0.55,
            color="Priority", color_discrete_map=PRIORITY_COLOURS,
        )
        fig.update_traces(textinfo="percent+label", textfont_size=13, pull=0.03)
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.18),
            margin=dict(l=10, r=10, t=10, b=40),
            height=280,
            annotations=[dict(
                text=f"<b>{df.height}</b><br>Patients",
                x=0.5, y=0.5, font_size=16, showarrow=False,
            )],
        )
        return plotly_html(fig)

    # ── Specialty box plot ────────────────────────────────────────────────────
    @render.ui
    def chart_specialty():
        df = filtered()
        if df.is_empty():
            return empty_state()
        fig = px.box(
            df, x="Specialty", y="Days_Waiting",
            color="Specialty", points="all",
            hover_data=["Hospital", "Priority"],
            labels={"Days_Waiting": "Days Waiting", "Specialty": ""},
            color_discrete_sequence=[NHS_BLUE, NHS_DARK, NHS_GREEN, NHS_AMBER, NHS_PURPLE],
        )
        fig.add_hline(
            y=RTT_THRESHOLD, line_dash="dash", line_color=NHS_RED,
            annotation_text="18-wk target",
            annotation_position="top right",
            annotation_font_color=NHS_RED,
        )
        fig.update_layout(
            showlegend=False, plot_bgcolor="white",
            margin=dict(l=10, r=10, t=10, b=10), height=280,
            yaxis=dict(showgrid=True, gridcolor="#eee"),
        )
        return plotly_html(fig)

    # ── Roster table ──────────────────────────────────────────────────────────
    @render.ui
    def chart_table():
        df = filtered()
        if df.is_empty():
            return empty_state()

        def row_col(days: int) -> str:
            if days > RTT_THRESHOLD:
                return NHS_RED
            if days > 84:
                return NHS_AMBER
            return "#ffffff"

        colours = [row_col(d) for d in df["Days_Waiting"].to_list()]
        fig = go.Figure(go.Table(
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
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
        return plotly_html(fig)


app = App(app_ui, server)
