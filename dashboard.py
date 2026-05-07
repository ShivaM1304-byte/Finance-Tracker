# ============================================================
# dashboard.py  —  Finance Tracker
# Reads your analysis outputs and builds a beautiful
# interactive HTML dashboard. Open outputs/dashboard.html
# in any browser — no internet needed!
# ============================================================

import pandas as pd
import json
import os

BASE       = os.path.dirname(os.path.abspath(__file__))
CLEAN_PATH = os.path.join(BASE, "outputs", "cleaned_transactions.csv")
OUT_PATH   = os.path.join(BASE, "outputs", "dashboard.html")


def build_data():
    df = pd.read_csv(CLEAN_PATH, parse_dates=["date"])

    months      = ["January", "February", "March", "April"]
    categories  = ["Food Delivery","Groceries","Transport",
                   "Shopping","Utilities","Entertainment","Health"]

    # Monthly totals per category
    pivot = (
        df.groupby(["month_name","category"])["amount"]
        .sum().unstack(fill_value=0)
        .reindex(months)
    )
    monthly_by_cat = {cat: [float(pivot.get(cat, pd.Series([0]*4)).iloc[i])
                             for i in range(4)] for cat in categories}
    monthly_totals = [float(pivot.sum(axis=1).iloc[i]) for i in range(4)]

    # Category totals (all months)
    cat_totals = {cat: float(df[df.category==cat]["amount"].sum())
                  for cat in categories}

    # Top 8 merchants
    top = (df.groupby("description")["amount"].sum()
             .sort_values(ascending=False).head(8))
    merchants = {"names": list(top.index), "amounts": [float(v) for v in top.values]}

    # Weekly
    weekly = df.groupby("week")["amount"].sum().reset_index()
    weekly_data = {"weeks": list(weekly.week.astype(str)),
                   "amounts": [float(v) for v in weekly.amount]}

    # Recent transactions (last 12)
    recent = df.sort_values("date", ascending=False).head(12)
    txns = []
    for _, r in recent.iterrows():
        txns.append({
            "date":     r["date"].strftime("%d %b"),
            "desc":     r["description"].title(),
            "cat":      r["category"],
            "amount":   int(r["amount"])
        })

    return {
        "months":        months,
        "categories":    categories,
        "monthly_totals": monthly_totals,
        "monthly_by_cat": monthly_by_cat,
        "cat_totals":    cat_totals,
        "merchants":     merchants,
        "weekly":        weekly_data,
        "txns":          txns,
        "total_spend":   float(df["amount"].sum()),
        "avg_monthly":   float(df["amount"].sum() / 4),
    }


def generate_html(data: dict) -> str:
    d = json.dumps(data)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Finance Tracker — Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:       #0e0f14;
    --surface:  #16181f;
    --card:     #1c1f2a;
    --border:   #2a2d3a;
    --accent:   #6c63ff;
    --accent2:  #ff6584;
    --green:    #43d9a2;
    --yellow:   #ffc542;
    --text:     #e8eaf0;
    --muted:    #6b7280;
    --font:     'Syne', sans-serif;
    --mono:     'DM Mono', monospace;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    min-height: 100vh;
    padding: 0 0 60px;
  }}

  /* ── HEADER ── */
  header {{
    padding: 32px 40px 24px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 16px;
    background: linear-gradient(135deg, #13141c 0%, #1a1b26 100%);
  }}
  header h1 {{
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(90deg, #fff 0%, var(--accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  header p {{ color: var(--muted); font-size: 13px; margin-top: 4px; }}
  .period-badge {{
    background: var(--card);
    border: 1px solid var(--border);
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    color: var(--muted);
    font-family: var(--mono);
  }}

  /* ── LAYOUT ── */
  .main {{ padding: 32px 40px; }}

  /* ── METRIC CARDS ── */
  .metrics {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 14px;
    margin-bottom: 28px;
  }}
  .metric {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    transition: transform .2s;
  }}
  .metric:hover {{ transform: translateY(-2px); }}
  .metric::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent-color, var(--accent));
  }}
  .metric .lbl {{
    font-size: 11px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-bottom: 10px;
  }}
  .metric .val {{
    font-size: 26px;
    font-weight: 700;
    color: var(--text);
    font-family: var(--mono);
  }}
  .metric .sub {{
    font-size: 11px;
    color: var(--muted);
    margin-top: 6px;
  }}

  /* ── GRID ── */
  .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }}
  .grid3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 16px; }}
  @media(max-width:900px) {{ .grid2,.grid3 {{ grid-template-columns: 1fr; }} }}

  /* ── CHART CARDS ── */
  .card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px;
  }}
  .card h3 {{
    font-size: 12px;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-bottom: 18px;
  }}
  .chart-box {{ position: relative; width: 100%; height: 220px; }}
  .chart-box-sm {{ position: relative; width: 100%; height: 180px; }}
  .chart-box-lg {{ position: relative; width: 100%; height: 260px; }}

  /* ── CATEGORY BARS ── */
  .cat-row {{
    display: flex; align-items: center;
    gap: 10px; margin-bottom: 12px;
  }}
  .cat-dot {{
    width: 8px; height: 8px;
    border-radius: 2px; flex-shrink: 0;
  }}
  .cat-name {{ font-size: 12px; color: var(--text); flex: 1; }}
  .cat-bar-bg {{
    height: 5px; background: var(--border);
    border-radius: 3px; flex: 2; overflow: hidden;
  }}
  .cat-fill {{ height: 100%; border-radius: 3px; transition: width .6s ease; }}
  .cat-amt {{
    font-size: 12px; color: var(--muted);
    font-family: var(--mono); min-width: 70px; text-align: right;
  }}

  /* ── TRANSACTIONS ── */
  .txn {{
    display: flex; align-items: center;
    gap: 12px; padding: 10px 0;
    border-bottom: 1px solid var(--border);
  }}
  .txn:last-child {{ border-bottom: none; }}
  .txn-icon {{
    width: 36px; height: 36px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; flex-shrink: 0;
  }}
  .txn-info {{ flex: 1; min-width: 0; }}
  .txn-name {{
    font-size: 13px; font-weight: 600;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }}
  .txn-meta {{ font-size: 11px; color: var(--muted); margin-top: 2px; }}
  .txn-badge {{
    font-size: 10px; padding: 2px 8px;
    border-radius: 10px; margin-left: 6px;
    font-family: var(--mono);
  }}
  .txn-amt {{
    font-size: 13px; font-weight: 600;
    color: var(--accent2); font-family: var(--mono);
  }}

  /* ── SIMULATOR ── */
  .sim-sliders {{ margin-bottom: 20px; }}
  .sim-row {{ margin-bottom: 16px; }}
  .sim-row label {{
    display: flex; justify-content: space-between;
    font-size: 12px; color: var(--muted); margin-bottom: 8px;
  }}
  .sim-row label span {{
    color: var(--green); font-family: var(--mono); font-weight: 500;
  }}
  input[type=range] {{
    width: 100%; height: 4px;
    -webkit-appearance: none; appearance: none;
    background: var(--border); border-radius: 2px; outline: none;
  }}
  input[type=range]::-webkit-slider-thumb {{
    -webkit-appearance: none;
    width: 16px; height: 16px;
    border-radius: 50%;
    background: var(--accent);
    cursor: pointer;
    box-shadow: 0 0 0 3px rgba(108,99,255,0.2);
  }}
  .sim-results {{
    display: grid; grid-template-columns: repeat(3,1fr); gap: 10px;
  }}
  .sim-box {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px; padding: 14px; text-align: center;
  }}
  .sim-box .s-lbl {{ font-size: 10px; color: var(--muted); margin-bottom: 6px; text-transform: uppercase; letter-spacing: .06em; }}
  .sim-box .s-val {{ font-size: 18px; font-weight: 700; color: var(--green); font-family: var(--mono); }}

  /* ── MONTH FILTER ── */
  .month-tabs {{ display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }}
  .mtab {{
    font-size: 12px; padding: 5px 14px;
    border-radius: 20px; border: 1px solid var(--border);
    background: transparent; color: var(--muted);
    cursor: pointer; font-family: var(--font); transition: all .15s;
  }}
  .mtab.active {{
    background: var(--accent); color: #fff;
    border-color: var(--accent);
  }}

  /* ── FOOTER ── */
  .footer {{
    text-align: center; padding: 32px;
    font-size: 12px; color: var(--muted);
    font-family: var(--mono);
  }}
</style>
</head>
<body>

<header>
  <div>
    <h1>Finance Tracker</h1>
    <p>Personal Spending Analytics Dashboard</p>
  </div>
  <div class="period-badge">Jan – Apr 2025 &nbsp;·&nbsp; 4 months</div>
</header>

<div class="main">

  <!-- METRIC CARDS -->
  <div class="metrics" id="metrics">
    <div class="metric" style="--accent-color:#6c63ff">
      <div class="lbl">Total Spent</div>
      <div class="val" id="m-total">—</div>
      <div class="sub">across all categories</div>
    </div>
    <div class="metric" style="--accent-color:#ff6584">
      <div class="lbl">Avg / Month</div>
      <div class="val" id="m-avg">—</div>
      <div class="sub">4-month average</div>
    </div>
    <div class="metric" style="--accent-color:#43d9a2">
      <div class="lbl">Biggest Category</div>
      <div class="val" id="m-bigcat" style="font-size:16px;padding-top:4px">—</div>
      <div class="sub" id="m-bigcat-amt">—</div>
    </div>
    <div class="metric" style="--accent-color:#ffc542">
      <div class="lbl">Transactions</div>
      <div class="val" id="m-txns">56</div>
      <div class="sub">debit entries</div>
    </div>
  </div>

  <!-- MONTH FILTER -->
  <div class="month-tabs">
    <button class="mtab" onclick="filterMonth(0)">January</button>
    <button class="mtab" onclick="filterMonth(1)">February</button>
    <button class="mtab" onclick="filterMonth(2)">March</button>
    <button class="mtab" onclick="filterMonth(3)">April</button>
    <button class="mtab active" onclick="filterMonth(-1)">All Months</button>
  </div>

  <!-- ROW 1: Trend + Donut -->
  <div class="grid2" style="margin-bottom:16px">
    <div class="card">
      <h3>Monthly Spending Trend</h3>
      <div class="chart-box"><canvas id="trendChart"></canvas></div>
    </div>
    <div class="card">
      <h3>Category Breakdown</h3>
      <div class="chart-box"><canvas id="donutChart"></canvas></div>
    </div>
  </div>

  <!-- ROW 2: Stacked + Weekly -->
  <div class="grid2" style="margin-bottom:16px">
    <div class="card">
      <h3>Stacked by Category</h3>
      <div class="chart-box"><canvas id="stackedChart"></canvas></div>
    </div>
    <div class="card">
      <h3>Weekly Spending</h3>
      <div class="chart-box"><canvas id="weeklyChart"></canvas></div>
    </div>
  </div>

  <!-- ROW 3: Category bars + Top merchants -->
  <div class="grid2" style="margin-bottom:16px">
    <div class="card">
      <h3>Category Analysis</h3>
      <div id="catBars" style="margin-top:6px"></div>
    </div>
    <div class="card">
      <h3>Top Merchants</h3>
      <div class="chart-box-lg"><canvas id="merchantChart"></canvas></div>
    </div>
  </div>

  <!-- ROW 4: Simulator + Transactions -->
  <div class="grid2">
    <div class="card">
      <h3>Savings Simulator</h3>
      <p style="font-size:12px;color:var(--muted);margin-bottom:18px">
        Drag to see how much you'd save in 3 months
      </p>
      <div class="sim-sliders">
        <div class="sim-row">
          <label>Food Delivery cut <span id="fd-lbl">20%</span></label>
          <input type="range" min="0" max="80" step="5" value="20" id="fdS" oninput="updateSim()">
        </div>
        <div class="sim-row">
          <label>Shopping cut <span id="sh-lbl">15%</span></label>
          <input type="range" min="0" max="80" step="5" value="15" id="shS" oninput="updateSim()">
        </div>
        <div class="sim-row">
          <label>Entertainment cut <span id="en-lbl">20%</span></label>
          <input type="range" min="0" max="80" step="5" value="20" id="enS" oninput="updateSim()">
        </div>
      </div>
      <div class="sim-results">
        <div class="sim-box"><div class="s-lbl">Per Month</div><div class="s-val" id="sim-mo">—</div></div>
        <div class="sim-box"><div class="s-lbl">3 Months</div><div class="s-val" id="sim-3m">—</div></div>
        <div class="sim-box"><div class="s-lbl">1 Year</div><div class="s-val" id="sim-yr">—</div></div>
      </div>
    </div>
    <div class="card">
      <h3>Recent Transactions</h3>
      <div id="txnList"></div>
    </div>
  </div>

</div>

<div class="footer">Finance Tracker &nbsp;·&nbsp; Built with Python + Chart.js &nbsp;·&nbsp; Your data stays local</div>

<script>
const DATA = {d};

const CAT_COLORS = {{
  "Food Delivery": "#ff6584",
  "Groceries":     "#43d9a2",
  "Transport":     "#6c63ff",
  "Shopping":      "#ffc542",
  "Utilities":     "#94a3b8",
  "Entertainment": "#f472b6",
  "Health":        "#fb923c",
}};

const CAT_ICONS = {{
  "Food Delivery":"🍱","Groceries":"🛒","Transport":"🚗",
  "Shopping":"📦","Utilities":"⚡","Entertainment":"🎬","Health":"💊"
}};

const INR = n => "₹" + Math.round(n).toLocaleString("en-IN");
let curMonth = -1;

// ── METRICS ──────────────────────────────────────────────────
function renderMetrics(mi) {{
  const totals = mi === -1
    ? DATA.monthly_totals
    : [DATA.monthly_totals[mi]];
  const total = totals.reduce((s,v)=>s+v,0);

  const catTotals = mi === -1
    ? DATA.cat_totals
    : Object.fromEntries(DATA.categories.map(c => [c, DATA.monthly_by_cat[c][mi]]));

  const bigCat = Object.entries(catTotals).sort((a,b)=>b[1]-a[1])[0];

  document.getElementById("m-total").textContent = INR(total);
  document.getElementById("m-avg").textContent   = INR(mi===-1 ? total/4 : total);
  document.getElementById("m-bigcat").textContent = bigCat[0];
  document.getElementById("m-bigcat-amt").textContent = INR(bigCat[1]);
}}

// ── CATEGORY BARS ─────────────────────────────────────────────
function renderCatBars(mi) {{
  const vals = Object.fromEntries(
    DATA.categories.map(c => [c, mi===-1
      ? DATA.monthly_by_cat[c].reduce((s,v)=>s+v,0)
      : DATA.monthly_by_cat[c][mi]])
  );
  const max = Math.max(...Object.values(vals));
  document.getElementById("catBars").innerHTML = DATA.categories.map(c => `
    <div class="cat-row">
      <div class="cat-dot" style="background:${{CAT_COLORS[c]}}"></div>
      <div class="cat-name">${{c}}</div>
      <div class="cat-bar-bg">
        <div class="cat-fill" style="width:${{(vals[c]/max*100).toFixed(1)}}%;background:${{CAT_COLORS[c]}}"></div>
      </div>
      <div class="cat-amt">${{INR(vals[c])}}</div>
    </div>
  `).join("");
}}

// ── TRANSACTIONS ──────────────────────────────────────────────
function renderTxns() {{
  document.getElementById("txnList").innerHTML = DATA.txns.map(t => `
    <div class="txn">
      <div class="txn-icon" style="background:${{CAT_COLORS[t.cat]}}22">
        ${{CAT_ICONS[t.cat] || "💳"}}
      </div>
      <div class="txn-info">
        <div class="txn-name">${{t.desc}}
          <span class="txn-badge" style="background:${{CAT_COLORS[t.cat]}}22;color:${{CAT_COLORS[t.cat]}}">${{t.cat}}</span>
        </div>
        <div class="txn-meta">${{t.date}}</div>
      </div>
      <div class="txn-amt">-${{INR(t.amount)}}</div>
    </div>
  `).join("");
}}

// ── CHARTS ───────────────────────────────────────────────────
const CHART_DEFAULTS = {{
  plugins: {{ legend: {{ display: false }}, tooltip: {{
    callbacks: {{ label: v => INR(v.raw) }}
  }}}},
  scales: {{
    x: {{ grid: {{ color:"rgba(255,255,255,0.05)" }}, ticks: {{ color:"#6b7280", font:{{size:11}} }} }},
    y: {{ grid: {{ color:"rgba(255,255,255,0.05)" }}, ticks: {{ color:"#6b7280", font:{{size:10}}, callback: v=>"₹"+(v/1000)+"k" }} }}
  }},
  responsive: true, maintainAspectRatio: false
}};

let trendC, donutC, stackedC, weeklyC, merchantC;

function initCharts() {{
  // Trend
  trendC = new Chart(document.getElementById("trendChart"), {{
    type: "bar",
    data: {{
      labels: DATA.months,
      datasets: [{{ label:"Total", data: DATA.monthly_totals,
        backgroundColor:["#6c63ff88","#6c63ffaa","#6c63ffcc","#6c63ff"],
        borderRadius:6, borderSkipped:false }}]
    }},
    options: {{ ...CHART_DEFAULTS }}
  }});

  // Donut
  donutC = new Chart(document.getElementById("donutChart"), {{
    type: "doughnut",
    data: {{
      labels: DATA.categories,
      datasets: [{{ data: DATA.categories.map(c=>DATA.cat_totals[c]),
        backgroundColor: DATA.categories.map(c=>CAT_COLORS[c]),
        borderWidth:2, borderColor:"#1c1f2a" }}]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false, cutout:"65%",
      plugins: {{
        legend: {{ display:true, position:"right",
          labels:{{ color:"#6b7280", font:{{size:10}}, boxWidth:10 }} }},
        tooltip: {{ callbacks: {{ label: v => ` ${{v.label}}: ${{INR(v.raw)}}` }} }}
      }}
    }}
  }});

  // Stacked
  stackedC = new Chart(document.getElementById("stackedChart"), {{
    type:"bar",
    data:{{
      labels: DATA.months,
      datasets: DATA.categories.map(c=>({{
        label:c, data:DATA.monthly_by_cat[c],
        backgroundColor: CAT_COLORS[c]+"cc",
        borderRadius:2, borderSkipped:false
      }}))
    }},
    options:{{ ...CHART_DEFAULTS, plugins:{{
      legend:{{ display:true, labels:{{ color:"#6b7280", font:{{size:9}}, boxWidth:8 }} }},
      tooltip:{{ callbacks:{{ label: v=>`${{v.dataset.label}}: ${{INR(v.raw)}}` }} }}
    }},
    scales:{{ x:{{ stacked:true, grid:{{color:"rgba(255,255,255,0.05)"}}, ticks:{{color:"#6b7280",font:{{size:11}}}} }},
              y:{{ stacked:true, grid:{{color:"rgba(255,255,255,0.05)"}}, ticks:{{color:"#6b7280",font:{{size:10}},callback:v=>"₹"+(v/1000)+"k"}} }} }} }}
  }});

  // Weekly
  weeklyC = new Chart(document.getElementById("weeklyChart"), {{
    type:"line",
    data:{{
      labels: DATA.weekly.weeks.map(w=>"Wk "+w),
      datasets:[{{ label:"Weekly Spend", data:DATA.weekly.amounts,
        borderColor:"#43d9a2", backgroundColor:"#43d9a215",
        borderWidth:2.5, pointRadius:4, pointBackgroundColor:"#43d9a2",
        tension:0.35, fill:true }}]
    }},
    options:{{ ...CHART_DEFAULTS }}
  }});

  // Merchants
  merchantC = new Chart(document.getElementById("merchantChart"), {{
    type:"bar",
    data:{{
      labels: DATA.merchants.names.map(n=>n.length>22?n.slice(0,22)+"…":n),
      datasets:[{{ label:"Total Spent", data:DATA.merchants.amounts,
        backgroundColor:"#6c63ff99", borderRadius:4, borderSkipped:false }}]
    }},
    options:{{ ...CHART_DEFAULTS, indexAxis:"y",
      plugins:{{ legend:{{display:false}}, tooltip:{{callbacks:{{label:v=>INR(v.raw)}}}} }} }}
  }});
}}

// ── MONTH FILTER ──────────────────────────────────────────────
function filterMonth(mi) {{
  curMonth = mi;
  document.querySelectorAll(".mtab").forEach((t,i) => {{
    t.classList.toggle("active", (i===mi)||(mi===-1&&i===4));
  }});

  const catVals = DATA.categories.map(c =>
    mi===-1 ? DATA.cat_totals[c] : DATA.monthly_by_cat[c][mi]
  );
  const monthTotals = mi===-1 ? DATA.monthly_totals : [DATA.monthly_totals[mi]];

  // Update trend chart
  if(mi===-1) {{
    trendC.data.labels = DATA.months;
    trendC.data.datasets[0].data = DATA.monthly_totals;
  }} else {{
    trendC.data.labels = DATA.categories;
    trendC.data.datasets[0].data = catVals;
    trendC.data.datasets[0].backgroundColor = DATA.categories.map(c=>CAT_COLORS[c]+"cc");
  }}
  trendC.update();

  // Update donut
  donutC.data.datasets[0].data = catVals;
  donutC.update();

  renderMetrics(mi);
  renderCatBars(mi);
}}

// ── SIMULATOR ─────────────────────────────────────────────────
function updateSim() {{
  const fd = parseInt(document.getElementById("fdS").value);
  const sh = parseInt(document.getElementById("shS").value);
  const en = parseInt(document.getElementById("enS").value);
  document.getElementById("fd-lbl").textContent = fd+"%";
  document.getElementById("sh-lbl").textContent = sh+"%";
  document.getElementById("en-lbl").textContent = en+"%";

  const avgFD = DATA.monthly_by_cat["Food Delivery"].reduce((s,v)=>s+v,0)/4;
  const avgSH = DATA.monthly_by_cat["Shopping"].reduce((s,v)=>s+v,0)/4;
  const avgEN = DATA.monthly_by_cat["Entertainment"].reduce((s,v)=>s+v,0)/4;

  const mo = Math.round(avgFD*fd/100 + avgSH*sh/100 + avgEN*en/100);
  document.getElementById("sim-mo").textContent = INR(mo);
  document.getElementById("sim-3m").textContent = INR(mo*3);
  document.getElementById("sim-yr").textContent = INR(mo*12);
}}

// ── INIT ──────────────────────────────────────────────────────
window.addEventListener("load", () => {{
  renderMetrics(-1);
  renderCatBars(-1);
  renderTxns();
  initCharts();
  updateSim();
}});
</script>
</body>
</html>"""


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  Finance Tracker — Dashboard Generator")
    print("="*55)

    data = build_data()
    html = generate_html(data)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ Dashboard saved → {OUT_PATH}")
    print("\n👉 How to open it:")
    print("   1. Open File Explorer")
    print("   2. Go to your FINANCE_TRACKER/outputs/ folder")
    print("   3. Double-click  dashboard.html")
    print("   4. It opens in Chrome/Edge — fully interactive!\n")