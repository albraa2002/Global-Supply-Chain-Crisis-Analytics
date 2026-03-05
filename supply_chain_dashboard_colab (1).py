# ============================================================
#  Global Shipping & Red Sea Crisis Analytics Dashboard
#  Single-Cell Google Colab Script
#  Run this entire cell at once — no dependencies to install
# ============================================================

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from IPython.display import display, HTML

# ── Reproducibility ─────────────────────────────────────────
np.random.seed(42)

# ============================================================
# STEP 1 — GENERATE REALISTIC SUPPLY CHAIN DATA (~8 000 rows)
# ============================================================

date_range = pd.date_range(start="2023-01-01", end="2025-12-31", freq="D")
n_days     = len(date_range)

# Daily shipment counts that sum to ~8 000 over 3 years
daily_counts = np.random.randint(6, 9, size=n_days)          # 7 ± 1 per day → ~7 700-8 100 rows

rows = []
for date, count in zip(date_range, daily_counts):
    is_post_crisis = date >= pd.Timestamp("2023-12-01")

    for _ in range(count):
        # Origin / Destination
        origin      = np.random.choice(["Asia", "Middle East"], p=[0.65, 0.35])
        destination = np.random.choice(["Europe", "North America"], p=[0.60, 0.40])

        # Route logic
        if is_post_crisis:
            route = np.random.choice(
                ["Suez Canal", "Cape of Good Hope"], p=[0.15, 0.85]
            )
        else:
            route = np.random.choice(
                ["Suez Canal", "Cape of Good Hope"], p=[0.90, 0.10]
            )

        # Expected transit days (base: Suez shorter, Cape longer)
        if route == "Suez Canal":
            expected_days = int(np.random.randint(20, 28))
        else:
            expected_days = int(np.random.randint(26, 34))

        # Actual transit days
        if is_post_crisis:
            delay         = int(np.random.randint(12, 26))
            actual_days   = expected_days + delay
        else:
            delay         = int(np.random.randint(0, 4))
            actual_days   = expected_days + delay

        # Freight cost
        if is_post_crisis:
            freight_cost = round(float(np.random.uniform(6_000, 12_000)), 2)
        else:
            freight_cost = round(float(np.random.uniform(2_000, 3_500)), 2)

        rows.append({
            "Shipment_Date"       : date,
            "Origin"              : origin,
            "Destination"         : destination,
            "Route_Taken"         : route,
            "Expected_Transit_Days": expected_days,
            "Actual_Transit_Days" : actual_days,
            "Freight_Cost_USD"    : freight_cost,
        })

df = pd.DataFrame(rows)
df["Shipment_Date"] = pd.to_datetime(df["Shipment_Date"])
print(f"✅  Dataset generated: {len(df):,} rows  |  {df['Shipment_Date'].min().date()} → {df['Shipment_Date'].max().date()}")

# ============================================================
# STEP 2 — CALCULATE KPIs
# ============================================================

crisis_start = pd.Timestamp("2023-12-01")

pre_df  = df[df["Shipment_Date"] <  crisis_start]
post_df = df[df["Shipment_Date"] >= crisis_start]

total_shipments      = len(df)
pre_avg_cost         = pre_df["Freight_Cost_USD"].mean()
post_avg_cost        = post_df["Freight_Cost_USD"].mean()
cost_spike_pct       = ((post_avg_cost - pre_avg_cost) / pre_avg_cost) * 100
post_df_copy         = post_df.copy()
post_df_copy["Delay"] = post_df_copy["Actual_Transit_Days"] - post_df_copy["Expected_Transit_Days"]
avg_delay_post       = post_df_copy["Delay"].mean()

print(f"\n📦  Total Shipments         : {total_shipments:,}")
print(f"💰  Pre-Crisis Avg Cost     : ${pre_avg_cost:,.0f}")
print(f"🚨  Post-Crisis Avg Cost    : ${post_avg_cost:,.0f}")
print(f"📈  Cost Spike              : +{cost_spike_pct:.1f}%")
print(f"⏱️   Avg Post-Crisis Delay   : +{avg_delay_post:.1f} days")

# ============================================================
# STEP 3 — CREATE 3 INDEPENDENT PLOTLY FIGURES
# ============================================================

# ── Industrial Color Palette ─────────────────────────────────
NAVY       = "#0f2d4e"
STEEL      = "#4a6fa5"
STEEL_LITE = "#7fa8d4"
ALERT_RED  = "#e63946"
ALERT_ORG  = "#f4a261"
CARD_BG    = "#1e293b"
GRID_CLR   = "#2d3f55"
TEXT_CLR   = "#e2e8f0"

PLOTLY_LAYOUT_BASE = dict(
    paper_bgcolor = CARD_BG,
    plot_bgcolor  = CARD_BG,
    font          = dict(color=TEXT_CLR, family="'Courier New', monospace"),
    margin        = dict(l=50, r=30, t=60, b=50),
    xaxis         = dict(
        gridcolor   = GRID_CLR,
        linecolor   = GRID_CLR,
        tickfont    = dict(color=TEXT_CLR),
        title_font  = dict(color=TEXT_CLR),
    ),
    yaxis         = dict(
        gridcolor   = GRID_CLR,
        linecolor   = GRID_CLR,
        tickfont    = dict(color=TEXT_CLR),
        title_font  = dict(color=TEXT_CLR),
    ),
)

# ── Fig 1: Monthly Average Freight Cost ──────────────────────
monthly_cost = (
    df.set_index("Shipment_Date")["Freight_Cost_USD"]
    .resample("ME")
    .mean()
    .reset_index()
)
monthly_cost.columns = ["Month", "Avg_Cost"]

fig_cost = go.Figure()

fig_cost.add_trace(go.Scatter(
    x          = monthly_cost["Month"],
    y          = monthly_cost["Avg_Cost"],
    mode       = "lines+markers",
    name       = "Avg Freight Cost",
    line       = dict(color=STEEL_LITE, width=2.5),
    marker     = dict(color=STEEL_LITE, size=5),
    fill       = "tozeroy",
    fillcolor  = "rgba(74,111,165,0.15)",
))

# Vertical crisis annotation
# NOTE: add_vline with string dates triggers a Plotly bug on datetime axes.
# Workaround: convert the date to Unix milliseconds (what Plotly uses internally).
import datetime
crisis_ts_ms = int(datetime.datetime(2023, 12, 1).timestamp() * 1000)

fig_cost.add_vline(
    x          = crisis_ts_ms,
    line_dash  = "dash",
    line_color = ALERT_RED,
    line_width = 2,
)
fig_cost.add_annotation(
    x          = crisis_ts_ms,
    y          = 0.97,
    yref       = "paper",
    xanchor    = "left",
    text       = "Red Sea Crisis Start",
    showarrow  = False,
    font       = dict(size=11, color=ALERT_RED),
    bgcolor    = "rgba(230,57,70,0.12)",
    borderpad  = 4,
)

fig_cost.update_layout(
    **PLOTLY_LAYOUT_BASE,
    title       = dict(text="Monthly Average Freight Cost (USD)", font=dict(size=16, color=TEXT_CLR)),
    xaxis_title = "Month",
    yaxis_title = "Avg Cost (USD)",
    showlegend  = False,
    height      = 380,
)

# ── Fig 2: Average Delay by Route ────────────────────────────
df["Delay_Days"] = df["Actual_Transit_Days"] - df["Expected_Transit_Days"]
delay_by_route   = df.groupby("Route_Taken")["Delay_Days"].mean().reset_index()

bar_colors = [ALERT_RED if r == "Cape of Good Hope" else STEEL
              for r in delay_by_route["Route_Taken"]]

fig_delay = go.Figure()
fig_delay.add_trace(go.Bar(
    x          = delay_by_route["Route_Taken"],
    y          = delay_by_route["Delay_Days"],
    marker     = dict(color=bar_colors, line=dict(width=0)),
    text       = [f"+{v:.1f} days" for v in delay_by_route["Delay_Days"]],
    textposition = "outside",
    textfont   = dict(color=TEXT_CLR),
))

_delay_yaxis = {**PLOTLY_LAYOUT_BASE["yaxis"], "range": [0, delay_by_route["Delay_Days"].max() * 1.35]}
_delay_layout = {**PLOTLY_LAYOUT_BASE, "yaxis": _delay_yaxis}
fig_delay.update_layout(
    **_delay_layout,
    title       = dict(text="Average Delay Days by Route Taken", font=dict(size=16, color=TEXT_CLR)),
    xaxis_title = "Route",
    yaxis_title = "Avg Delay (Days)",
    showlegend  = False,
    height      = 380,
)

# ── Fig 3: Route Distribution (Post-Crisis Only) ─────────────
post_route = post_df["Route_Taken"].value_counts().reset_index()
post_route.columns = ["Route", "Count"]

fig_route = go.Figure()
fig_route.add_trace(go.Pie(
    labels       = post_route["Route"],
    values       = post_route["Count"],
    hole         = 0.5,
    marker       = dict(colors=[ALERT_RED, STEEL], line=dict(color=CARD_BG, width=3)),
    textinfo     = "label+percent",
    textfont     = dict(color=TEXT_CLR, size=13),
    hovertemplate= "<b>%{label}</b><br>Shipments: %{value:,}<br>Share: %{percent}<extra></extra>",
))

fig_route.update_layout(
    **{k: v for k, v in PLOTLY_LAYOUT_BASE.items() if k not in ("xaxis", "yaxis")},
    title      = dict(text="Route Distribution (Post-Crisis Only)", font=dict(size=16, color=TEXT_CLR)),
    showlegend = True,
    legend     = dict(font=dict(color=TEXT_CLR), bgcolor="rgba(0,0,0,0)"),
    height     = 380,
)

print("\n✅  All 3 Plotly figures created successfully.")

# ============================================================
# STEP 4 — BUILD PURE HTML/CSS DASHBOARD
# ============================================================

fig_cost_html  = fig_cost.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})
fig_delay_html = fig_delay.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})
fig_route_html = fig_route.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})

# Format KPI values
kpi_total    = f"{total_shipments:,}"
kpi_spike    = f"+{cost_spike_pct:.1f}%"
kpi_delay    = f"+{avg_delay_post:.1f} days"
kpi_pre_cost = f"${pre_avg_cost:,.0f}"
kpi_post_cost= f"${post_avg_cost:,.0f}"

html_dashboard = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Global Shipping & Red Sea Crisis Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg-deep:    #0f172a;
      --bg-card:    #1e293b;
      --bg-card2:   #162032;
      --border:     #2d3f55;
      --navy:       #0f2d4e;
      --steel:      #4a6fa5;
      --steel-lite: #7fa8d4;
      --alert-red:  #e63946;
      --alert-org:  #f4a261;
      --text:       #e2e8f0;
      --text-muted: #94a3b8;
      --mono:       'Share Tech Mono', monospace;
      --sans:       'Rajdhani', sans-serif;
    }}

    html, body {{
      background: var(--bg-deep);
      color: var(--text);
      font-family: var(--sans);
      min-height: 100vh;
    }}

    /* ── Header ── */
    .header {{
      padding: 28px 40px 16px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      background: linear-gradient(90deg, rgba(15,45,78,0.6) 0%, rgba(15,23,42,0) 100%);
    }}
    .header-left h1 {{
      font-size: 1.85rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      line-height: 1.1;
      color: var(--text);
    }}
    .header-left h1 span {{ color: var(--alert-red); }}
    .header-left p {{
      font-family: var(--mono);
      font-size: 0.72rem;
      color: var(--text-muted);
      margin-top: 4px;
      letter-spacing: 0.08em;
    }}
    .badge {{
      font-family: var(--mono);
      font-size: 0.68rem;
      letter-spacing: 0.1em;
      padding: 5px 14px;
      border-radius: 2px;
      border: 1px solid var(--alert-red);
      color: var(--alert-red);
      background: rgba(230,57,70,0.08);
      text-transform: uppercase;
    }}

    /* ── Layout ── */
    .dashboard {{
      max-width: 1400px;
      margin: 0 auto;
      padding: 28px 32px 40px;
      display: grid;
      gap: 20px;
    }}

    /* ── KPI Row ── */
    .kpi-row {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }}
    .kpi-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 20px 24px;
      position: relative;
      overflow: hidden;
    }}
    .kpi-card::before {{
      content: '';
      position: absolute;
      left: 0; top: 0; bottom: 0;
      width: 3px;
      background: var(--steel);
    }}
    .kpi-card.alert::before  {{ background: var(--alert-red); }}
    .kpi-card.warning::before{{ background: var(--alert-org); }}

    .kpi-label {{
      font-family: var(--mono);
      font-size: 0.65rem;
      letter-spacing: 0.12em;
      color: var(--text-muted);
      text-transform: uppercase;
      margin-bottom: 8px;
    }}
    .kpi-value {{
      font-size: 2.4rem;
      font-weight: 700;
      line-height: 1;
      letter-spacing: -0.01em;
    }}
    .kpi-value.red     {{ color: var(--alert-red); }}
    .kpi-value.orange  {{ color: var(--alert-org); }}
    .kpi-value.steel   {{ color: var(--steel-lite); }}
    .kpi-sub {{
      font-family: var(--mono);
      font-size: 0.68rem;
      color: var(--text-muted);
      margin-top: 6px;
    }}

    /* ── Chart Cards ── */
    .chart-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px 4px 4px;
    }}
    .chart-full {{ grid-column: 1 / -1; }}

    .chart-row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }}

    /* ── Footer ── */
    .footer {{
      text-align: center;
      font-family: var(--mono);
      font-size: 0.62rem;
      color: var(--text-muted);
      letter-spacing: 0.1em;
      padding: 12px 0 0;
      border-top: 1px solid var(--border);
    }}

    /* ── Plotly container sizing ── */
    .chart-card > div {{ width: 100% !important; }}
  </style>
</head>
<body>

  <!-- HEADER -->
  <header class="header">
    <div class="header-left">
      <h1>Global Shipping &amp; <span>Red Sea Crisis</span> Analytics</h1>
      <p>Data Range: Jan 2023 – Dec 2025  ·  Generated {total_shipments:,} Shipment Records  ·  Crisis Onset: Dec 2023</p>
    </div>
    <div class="badge">🚨 Crisis Impact Active</div>
  </header>

  <!-- DASHBOARD GRID -->
  <main class="dashboard">

    <!-- KPI ROW -->
    <div class="kpi-row">

      <div class="kpi-card">
        <div class="kpi-label">Total Shipments Analyzed</div>
        <div class="kpi-value steel">{kpi_total}</div>
        <div class="kpi-sub">Jan 2023 – Dec 2025 ·  All routes</div>
      </div>

      <div class="kpi-card alert">
        <div class="kpi-label">Freight Cost Spike (Post-Crisis)</div>
        <div class="kpi-value red">{kpi_spike}</div>
        <div class="kpi-sub">Pre: {kpi_pre_cost} avg  →  Post: {kpi_post_cost} avg</div>
      </div>

      <div class="kpi-card warning">
        <div class="kpi-label">Avg Delay Days (Post-Crisis)</div>
        <div class="kpi-value orange">{kpi_delay}</div>
        <div class="kpi-sub">Actual vs Expected Transit  ·  Cape of Good Hope rerouting</div>
      </div>

    </div>

    <!-- FULL-WIDTH COST CHART -->
    <div class="chart-card chart-full">
      {fig_cost_html}
    </div>

    <!-- SIDE-BY-SIDE CHARTS -->
    <div class="chart-row">
      <div class="chart-card">
        {fig_delay_html}
      </div>
      <div class="chart-card">
        {fig_route_html}
      </div>
    </div>

    <!-- FOOTER -->
    <div class="footer">
      SUPPLY CHAIN INTELLIGENCE DASHBOARD  ·  BUILT WITH PLOTLY &amp; PYTHON  ·  RED SEA / HOUTHI CRISIS IMPACT ANALYSIS
    </div>

  </main>

</body>
</html>"""

print(f"\n✅  HTML dashboard assembled  ({len(html_dashboard):,} characters)")

# ============================================================
# STEP 5 — SAVE FILE & AUTO-DOWNLOAD IN COLAB
# ============================================================

output_filename = "Supply_Chain_Crisis_Dashboard.html"

with open(output_filename, "w", encoding="utf-8") as f:
    f.write(html_dashboard)

print(f"✅  Saved: {output_filename}")

# Auto-download in Google Colab
try:
    from google.colab import files
    files.download(output_filename)
    print("⬇️   Download triggered in Colab.")
except ImportError:
    print("ℹ️   Not running in Colab — file saved locally as:", output_filename)

# ── Optional: Preview inside Colab notebook ─────────────────
try:
    from IPython.display import IFrame
    display(IFrame(src=output_filename, width="100%", height="900px"))
except Exception:
    pass

print("\n🎉  All done!  Open Supply_Chain_Crisis_Dashboard.html in your browser.")
