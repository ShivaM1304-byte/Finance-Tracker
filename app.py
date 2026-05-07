# ============================================================
# app.py  —  Finance Tracker
# Full Streamlit Web App — runs in your browser!
# Command: streamlit run app.py
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# ── Make all modules importable (bulletproof) ────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(BASE, "src")

# Add BOTH root and src to path BEFORE any imports
for p in [BASE, SRC]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Change working directory to project root so all relative
# paths inside the modules resolve correctly
os.chdir(BASE)

from categorize import load_and_clean
from budget import check_budget, get_monthly_spending
from recurring import detect_recurring

# ── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title = "Finance Tracker",
    page_icon  = "💳",
    layout     = "wide",
    initial_sidebar_state = "expanded"
)

# ── CUSTOM CSS ───────────────────────────────────────────────
st.markdown("""
<style>
  /* Main background */
  .stApp { background-color: #0e0f14; color: #e8eaf0; }

  /* Cards */
  div[data-testid="metric-container"] {
    background: #1c1f2a;
    border: 1px solid #2a2d3a;
    border-radius: 12px;
    padding: 16px;
  }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background: #16181f;
    border-right: 1px solid #2a2d3a;
  }

  /* Headers */
  h1, h2, h3 { color: #e8eaf0 !important; }

  /* Section divider */
  hr { border-color: #2a2d3a; }

  /* Success / warning / error boxes */
  .stAlert { border-radius: 10px; }

  /* Tab styling */
  .stTabs [data-baseweb="tab"] {
    background: #1c1f2a;
    border-radius: 8px 8px 0 0;
    color: #6b7280;
    padding: 8px 20px;
  }
  .stTabs [aria-selected="true"] {
    background: #6c63ff !important;
    color: white !important;
  }
</style>
""", unsafe_allow_html=True)

# ── COLORS ───────────────────────────────────────────────────
CAT_COLORS = {
    "Food Delivery":  "#ff6584",
    "Groceries":      "#43d9a2",
    "Transport":      "#6c63ff",
    "Shopping":       "#ffc542",
    "Utilities":      "#94a3b8",
    "Entertainment":  "#f472b6",
    "Health":         "#fb923c",
    "Food & Dining":  "#f97316",
    "Others":         "#64748b",
}

MONTH_ORDER = ["January","February","March","April",
               "May","June","July","August",
               "September","October","November","December"]

# ── DEFAULT BUDGETS ──────────────────────────────────────────
DEFAULT_BUDGETS = {
    "Food Delivery":  2000,
    "Groceries":      4000,
    "Transport":      1500,
    "Shopping":       5000,
    "Utilities":      3000,
    "Entertainment":  1500,
    "Health":         1000,
    "Food & Dining":  2000,
    "Others":         1000,
}


# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 💳 Finance Tracker")
    st.markdown("---")

    # ── FILE UPLOAD ──────────────────────────────────────────
    st.markdown("### 📂 Upload Bank Statement")
    uploaded = st.file_uploader(
        "Drop your bank CSV here",
        type=["csv"],
        help="Upload your Kotak / any bank CSV statement"
    )

    st.markdown("---")

    # ── BUDGET SETTINGS ──────────────────────────────────────
    st.markdown("### 💰 Monthly Budgets (₹)")
    budgets = {}
    for cat, default in DEFAULT_BUDGETS.items():
        budgets[cat] = st.number_input(
            cat, min_value=0, max_value=100000,
            value=default, step=500, key=f"budget_{cat}"
        )

    st.markdown("---")
    st.markdown("### 📅 Filter by Month")
    month_filter = st.selectbox(
        "Select month",
        ["All Months"] + MONTH_ORDER
    )

    st.markdown("---")
    st.caption("Finance Tracker v2.0 · Built with Python & Streamlit")


# ════════════════════════════════════════════════════════════
# LOAD DATA
# ════════════════════════════════════════════════════════════
@st.cache_data
def load_from_upload(file_bytes: bytes) -> pd.DataFrame:
    """Load and clean uploaded CSV file."""
    import io, tempfile, os

    # Save to temp file so load_and_clean can read it
    with tempfile.NamedTemporaryFile(delete=False,
                                     suffix=".csv",
                                     mode="wb") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        debits, _ = load_and_clean(tmp_path)
    finally:
        os.unlink(tmp_path)

    return debits


@st.cache_data
def load_from_disk() -> pd.DataFrame:
    """Load cleaned transactions from disk (fallback)."""
    path = os.path.join(BASE, "outputs", "cleaned_transactions.csv")
    if os.path.exists(path):
        return pd.read_csv(path, parse_dates=["date"])
    return pd.DataFrame()


# Decide data source
if uploaded is not None:
    try:
        df = load_from_upload(uploaded.read())
        st.sidebar.success(f"✅ Loaded {len(df)} transactions")
    except Exception as e:
        st.sidebar.error(f"❌ Error: {e}")
        df = load_from_disk()
else:
    df = load_from_disk()

# Apply month filter
if month_filter != "All Months" and not df.empty:
    df_filtered = df[df["month_name"] == month_filter].copy()
else:
    df_filtered = df.copy()


# ════════════════════════════════════════════════════════════
# MAIN CONTENT
# ════════════════════════════════════════════════════════════
st.markdown("# 💳 Finance Tracker Dashboard")
st.markdown(f"**{month_filter}** · {len(df_filtered)} transactions")
st.markdown("---")

if df_filtered.empty:
    st.warning("⚠️ No data found. Upload your bank CSV using the sidebar!")
    st.stop()

# ── METRIC CARDS ─────────────────────────────────────────────
total_spent   = df_filtered["amount"].sum()
avg_per_day   = total_spent / max(df_filtered["date"].nunique(), 1)
top_cat       = df_filtered.groupby("category")["amount"].sum().idxmax()
top_cat_amt   = df_filtered.groupby("category")["amount"].sum().max()
num_months    = df_filtered["month"].nunique()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💸 Total Spent",
              f"₹{total_spent:,.0f}",
              delta=None)
with col2:
    st.metric("📅 Avg per Day",
              f"₹{avg_per_day:,.0f}")
with col3:
    st.metric("🏆 Top Category",
              top_cat,
              delta=f"₹{top_cat_amt:,.0f}")
with col4:
    st.metric("📦 Transactions",
              len(df_filtered))

st.markdown("---")

# ── TABS ─────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "💰 Budget Alerts",
    "📅 Recurring Payments",
    "📋 Transactions"
])


# ════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ════════════════════════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns(2)

    # ── Monthly Trend ─────────────────────────────────────────
    with col_left:
        st.markdown("#### 📈 Monthly Spending Trend")
        monthly = (
            df.groupby("month_name")["amount"].sum()
            .reindex([m for m in MONTH_ORDER if m in df["month_name"].unique()])
            .reset_index()
        )
        monthly.columns = ["Month", "Amount"]
        fig = px.bar(
            monthly, x="Month", y="Amount",
            color="Amount",
            color_continuous_scale=["#3b4fd8","#6c63ff"],
            text=monthly["Amount"].apply(lambda x: f"₹{x:,.0f}"),
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            paper_bgcolor="#1c1f2a", plot_bgcolor="#1c1f2a",
            font_color="#e8eaf0", showlegend=False,
            coloraxis_showscale=False,
            margin=dict(t=20, b=20),
            yaxis=dict(tickprefix="₹", gridcolor="#2a2d3a"),
            xaxis=dict(gridcolor="#2a2d3a"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Category Donut ────────────────────────────────────────
    with col_right:
        st.markdown("#### 🍩 Category Breakdown")
        cat_data = (
            df_filtered.groupby("category")["amount"]
            .sum().reset_index()
            .sort_values("amount", ascending=False)
        )
        fig2 = px.pie(
            cat_data, values="amount", names="category",
            hole=0.6,
            color="category",
            color_discrete_map=CAT_COLORS,
        )
        fig2.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate="%{label}<br>₹%{value:,.0f}<extra></extra>"
        )
        fig2.update_layout(
            paper_bgcolor="#1c1f2a",
            font_color="#e8eaf0",
            margin=dict(t=20, b=20),
            legend=dict(font=dict(size=11)),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Stacked Bar ───────────────────────────────────────────
    st.markdown("#### 📊 Monthly Spending by Category")
    pivot = (
        df.groupby(["month_name","category"])["amount"]
        .sum().unstack(fill_value=0)
        .reindex([m for m in MONTH_ORDER if m in df["month_name"].unique()])
    )
    fig3 = go.Figure()
    for cat in pivot.columns:
        fig3.add_trace(go.Bar(
            name=cat, x=pivot.index,
            y=pivot[cat],
            marker_color=CAT_COLORS.get(cat, "#888"),
            hovertemplate=f"{cat}<br>₹%{{y:,.0f}}<extra></extra>"
        ))
    fig3.update_layout(
        barmode="stack",
        paper_bgcolor="#1c1f2a", plot_bgcolor="#1c1f2a",
        font_color="#e8eaf0",
        margin=dict(t=20, b=20),
        yaxis=dict(tickprefix="₹", gridcolor="#2a2d3a"),
        xaxis=dict(gridcolor="#2a2d3a"),
        legend=dict(font=dict(size=10)),
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Weekly Trend ──────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 📉 Weekly Spending")
        weekly = (
            df_filtered.groupby("week")["amount"]
            .sum().reset_index()
        )
        weekly.columns = ["Week", "Amount"]
        fig4 = px.line(
            weekly, x="Week", y="Amount",
            markers=True,
            color_discrete_sequence=["#43d9a2"],
        )
        fig4.update_layout(
            paper_bgcolor="#1c1f2a", plot_bgcolor="#1c1f2a",
            font_color="#e8eaf0",
            margin=dict(t=20, b=20),
            yaxis=dict(tickprefix="₹", gridcolor="#2a2d3a"),
            xaxis=dict(gridcolor="#2a2d3a"),
        )
        fig4.update_traces(fill="tozeroy", fillcolor="rgba(67,217,162,0.1)")
        st.plotly_chart(fig4, use_container_width=True)

    # ── Top Merchants ─────────────────────────────────────────
    with col_b:
        st.markdown("#### 🏪 Top Merchants")
        top_merchants = (
            df_filtered.groupby("description")["amount"]
            .sum().sort_values(ascending=True).tail(8)
            .reset_index()
        )
        fig5 = px.bar(
            top_merchants, x="amount", y="description",
            orientation="h",
            color_discrete_sequence=["#6c63ff"],
            text=top_merchants["amount"].apply(lambda x: f"₹{x:,.0f}"),
        )
        fig5.update_traces(textposition="outside")
        fig5.update_layout(
            paper_bgcolor="#1c1f2a", plot_bgcolor="#1c1f2a",
            font_color="#e8eaf0",
            margin=dict(t=20, b=20, l=10),
            xaxis=dict(tickprefix="₹", gridcolor="#2a2d3a"),
            yaxis=dict(gridcolor="#2a2d3a"),
        )
        st.plotly_chart(fig5, use_container_width=True)

    # ── Savings Simulator ─────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 💰 Savings Simulator")
    sim_col1, sim_col2, sim_col3 = st.columns(3)

    with sim_col1:
        fd_cut = st.slider("Food Delivery cut %", 0, 80, 20, 5)
    with sim_col2:
        sh_cut = st.slider("Shopping cut %", 0, 80, 15, 5)
    with sim_col3:
        en_cut = st.slider("Entertainment cut %", 0, 80, 20, 5)

    avg_fd = df.groupby("month")["amount"].sum().mean() * \
             (df_filtered[df_filtered["category"]=="Food Delivery"]["amount"].sum() /
              max(df_filtered["amount"].sum(), 1))
    avg_sh = df.groupby("month")["amount"].sum().mean() * \
             (df_filtered[df_filtered["category"]=="Shopping"]["amount"].sum() /
              max(df_filtered["amount"].sum(), 1))
    avg_en = df.groupby("month")["amount"].sum().mean() * \
             (df_filtered[df_filtered["category"]=="Entertainment"]["amount"].sum() /
              max(df_filtered["amount"].sum(), 1))

    mo_save = (avg_fd * fd_cut/100) + (avg_sh * sh_cut/100) + (avg_en * en_cut/100)

    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Monthly Saving",  f"₹{mo_save:,.0f}")
    with s2:
        st.metric("3-Month Saving",  f"₹{mo_save*3:,.0f}")
    with s3:
        st.metric("Annual Saving",   f"₹{mo_save*12:,.0f}")


# ════════════════════════════════════════════════════════════
# TAB 2 — BUDGET ALERTS
# ════════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### 💰 Budget vs Actual Spending")
    st.caption("Adjust your budgets in the sidebar →")

    if month_filter == "All Months":
        check_month = int(df["month"].max())
        check_name  = df[df["month"]==check_month]["month_name"].iloc[0]
        st.info(f"Showing most recent month: **{check_name}**. "
                f"Select a specific month in the sidebar to change.")
    else:
        check_month = df[df["month_name"]==month_filter]["month"].iloc[0] \
                      if len(df[df["month_name"]==month_filter]) > 0 else None
        check_name  = month_filter

    if check_month:
        spending = get_monthly_spending(df, int(check_month))
        results  = check_budget(spending, budgets)

        over  = [r for r in results if r["status"] == "OVER BUDGET"]
        warn  = [r for r in results if r["status"] == "WARNING"]
        safe  = [r for r in results if r["status"] == "SAFE"]

        if over:
            st.error(f"🚨 {len(over)} categor{'y' if len(over)==1 else 'ies'} over budget!")
        if warn:
            st.warning(f"⚠️ {len(warn)} categor{'y' if len(warn)==1 else 'ies'} approaching limit!")
        if not over and not warn:
            st.success("🎉 All categories within budget this month!")

        st.markdown("---")

        # Budget progress bars
        for r in results:
            pct   = min(r["pct"], 100)
            color = "🔴" if r["status"]=="OVER BUDGET" else \
                    "🟡" if r["status"]=="WARNING" else "🟢"

            col_name, col_bar, col_info = st.columns([2, 4, 2])
            with col_name:
                st.markdown(f"{color} **{r['category']}**")
            with col_bar:
                st.progress(int(pct))
            with col_info:
                st.markdown(
                    f"₹{r['spent']:,.0f} / ₹{r['limit']:,.0f} "
                    f"(**{r['pct']:.0f}%**)"
                )

        # Budget summary chart
        st.markdown("---")
        st.markdown("#### Budget vs Actual — Bar Chart")
        budget_df = pd.DataFrame(results)
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(
            name="Budget",
            x=budget_df["category"],
            y=budget_df["limit"],
            marker_color="#2a2d3a",
        ))
        fig_b.add_trace(go.Bar(
            name="Actual",
            x=budget_df["category"],
            y=budget_df["spent"],
            marker_color=[
                "#ff6584" if r["status"]=="OVER BUDGET" else
                "#ffc542" if r["status"]=="WARNING" else
                "#43d9a2"
                for r in results
            ],
        ))
        fig_b.update_layout(
            barmode="group",
            paper_bgcolor="#1c1f2a", plot_bgcolor="#1c1f2a",
            font_color="#e8eaf0",
            yaxis=dict(tickprefix="₹", gridcolor="#2a2d3a"),
            xaxis=dict(gridcolor="#2a2d3a"),
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig_b, use_container_width=True)


# ════════════════════════════════════════════════════════════
# TAB 3 — RECURRING PAYMENTS
# ════════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### 📅 Recurring Payment Detector")
    st.caption("Merchants appearing in 2 or more months are flagged as recurring.")

    summary = detect_recurring(df, min_months=2)

    if summary.empty:
        st.success("✅ No recurring payments detected!")
    else:
        total_yearly = summary["yearly_projection"].sum()

        r1, r2, r3 = st.columns(3)
        with r1:
            st.metric("Recurring Payments Found", len(summary))
        with r2:
            st.metric("Total Per Month", f"₹{total_yearly/12:,.0f}")
        with r3:
            st.metric("Total Per Year", f"₹{total_yearly:,.0f}")

        st.markdown("---")

        # Display each recurring payment
        for _, row in summary.iterrows():
            yearly = row["yearly_projection"]
            color  = "🔴" if yearly > 10000 else \
                     "🟡" if yearly > 5000  else "🟢"

            with st.expander(
                f"{color} {row['merchant']} — "
                f"₹{row['avg_monthly_amount']:,.0f}/month · "
                f"₹{yearly:,.0f}/year"
            ):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Avg/Month",
                              f"₹{row['avg_monthly_amount']:,.0f}")
                with c2:
                    st.metric("Total Paid",
                              f"₹{row['total_paid']:,.0f}")
                with c3:
                    st.metric("Months Seen",
                              int(row["months_appeared"]))
                st.caption(f"📅 Seen in: {row['months_list']}")

        # Yearly cost bar chart
        st.markdown("---")
        st.markdown("#### Yearly Cost by Recurring Merchant")
        fig_r = px.bar(
            summary.sort_values("yearly_projection", ascending=True),
            x="yearly_projection", y="merchant",
            orientation="h",
            color="yearly_projection",
            color_continuous_scale=["#43d9a2","#ffc542","#ff6584"],
            text=summary.sort_values("yearly_projection", ascending=True)
                        ["yearly_projection"].apply(lambda x: f"₹{x:,.0f}"),
        )
        fig_r.update_traces(textposition="outside")
        fig_r.update_layout(
            paper_bgcolor="#1c1f2a", plot_bgcolor="#1c1f2a",
            font_color="#e8eaf0",
            coloraxis_showscale=False,
            margin=dict(t=20, b=20, l=10),
            xaxis=dict(tickprefix="₹", gridcolor="#2a2d3a"),
            yaxis=dict(gridcolor="#2a2d3a"),
        )
        st.plotly_chart(fig_r, use_container_width=True)


# ════════════════════════════════════════════════════════════
# TAB 4 — TRANSACTIONS
# ════════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### 📋 All Transactions")

    # Search box
    search = st.text_input("🔍 Search transactions", "")

    # Category filter
    all_cats = ["All"] + sorted(df_filtered["category"].unique().tolist())
    cat_pick = st.selectbox("Filter by category", all_cats)

    # Apply filters
    display = df_filtered.copy()
    if search:
        display = display[
            display["description"].str.contains(search, case=False, na=False)
        ]
    if cat_pick != "All":
        display = display[display["category"] == cat_pick]

    # Format for display
    display_out = display[["date","description","amount","category"]].copy()
    display_out["date"]   = display_out["date"].dt.strftime("%d %b %Y")
    display_out["amount"] = display_out["amount"].apply(lambda x: f"₹{x:,.0f}")
    display_out.columns   = ["Date","Description","Amount","Category"]
    display_out = display_out.sort_values("Date", ascending=False)

    st.dataframe(
        display_out,
        use_container_width=True,
        hide_index=True,
        height=500,
    )

    st.caption(f"Showing {len(display_out)} transactions")

    # Download button
    csv = display.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download filtered transactions as CSV",
        data=csv,
        file_name="filtered_transactions.csv",
        mime="text/csv",
    )