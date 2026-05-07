# ============================================================
# visualize.py  —  Finance Tracker
# Step 3: Generate all charts and save them as PNG files
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import os

# ── STYLE CONFIG ─────────────────────────────────────────────
COLORS = {
    "Food Delivery": "#D85A30",
    "Groceries":     "#1D9E75",
    "Transport":     "#378ADD",
    "Shopping":      "#BA7517",
    "Utilities":     "#888780",
    "Entertainment": "#7F77DD",
    "Health":        "#D4537E",
    "Others":        "#B4B2A9",
    "Income":        "#3B6D11",
}

plt.rcParams.update({
    "figure.facecolor":  "#FAFAFA",
    "axes.facecolor":    "#FAFAFA",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "font.family":       "DejaVu Sans",
    "axes.titlesize":    13,
    "axes.titleweight":  "bold",
    "axes.labelsize":    10,
})

MONTH_ORDER = ["January", "February", "March", "April"]


def rupee(x, _):
    """Format y-axis labels as ₹ thousands."""
    return f"₹{int(x/1000)}k"


# ── CHART 1: Monthly Total Spending Bar Chart ─────────────────
def chart_monthly_trend(df: pd.DataFrame, out_dir: str):
    monthly = df.groupby("month_name")["amount"].sum().reindex(MONTH_ORDER)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(
        monthly.index, monthly.values,
        color=["#B5D4F4", "#85B7EB", "#378ADD", "#185FA5"],
        width=0.55, zorder=2
    )
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(rupee))
    ax.set_title("Monthly Total Spending")
    ax.set_xlabel("Month")
    ax.set_ylabel("Amount (₹)")
    ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=1)

    # Add value labels on top of each bar
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + 300,
            f"₹{h:,.0f}",
            ha="center", va="bottom", fontsize=9, fontweight="bold"
        )

    fig.tight_layout()
    path = os.path.join(out_dir, "chart_01_monthly_trend.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Saved: {path}")


# ── CHART 2: Category Donut Chart ────────────────────────────
def chart_category_donut(df: pd.DataFrame, out_dir: str):
    cat_totals = (
        df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    colors = [COLORS.get(c, "#CCCCCC") for c in cat_totals.index]
    fig, ax = plt.subplots(figsize=(7, 7))

    wedges, texts, autotexts = ax.pie(
        cat_totals.values,
        labels=None,
        colors=colors,
        autopct="%1.1f%%",
        pctdistance=0.78,
        startangle=140,
        wedgeprops={"linewidth": 2, "edgecolor": "#FAFAFA"},
    )

    for at in autotexts:
        at.set_fontsize(8)
        at.set_color("white")
        at.set_fontweight("bold")

    # Legend
    legend_labels = [
        f"{cat}  ₹{amt:,.0f}"
        for cat, amt in zip(cat_totals.index, cat_totals.values)
    ]
    ax.legend(
        wedges, legend_labels,
        loc="lower center", bbox_to_anchor=(0.5, -0.12),
        ncol=2, fontsize=8.5, frameon=False
    )

    # Centre hole label
    ax.text(0, 0, f"₹{cat_totals.sum():,.0f}\nTotal",
            ha="center", va="center", fontsize=12, fontweight="bold")

    ax.set_title("Spending by Category (4 months)", pad=20)
    fig.tight_layout()
    path = os.path.join(out_dir, "chart_02_category_donut.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Saved: {path}")


# ── CHART 3: Stacked Bar — Category × Month ──────────────────
def chart_stacked_monthly(df: pd.DataFrame, out_dir: str):
    pivot = (
        df.groupby(["month_name", "category"])["amount"]
        .sum()
        .unstack(fill_value=0)
        .reindex(MONTH_ORDER)
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    bottom = np.zeros(len(pivot))

    for cat in pivot.columns:
        vals = pivot[cat].values
        ax.bar(
            pivot.index, vals, bottom=bottom,
            label=cat, color=COLORS.get(cat, "#CCCCCC"),
            width=0.55, zorder=2
        )
        bottom += vals

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(rupee))
    ax.set_title("Monthly Spending — Stacked by Category")
    ax.set_xlabel("Month")
    ax.set_ylabel("Amount (₹)")
    ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=1)
    ax.legend(
        loc="upper left", fontsize=8,
        frameon=True, framealpha=0.7
    )

    fig.tight_layout()
    path = os.path.join(out_dir, "chart_03_stacked_monthly.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Saved: {path}")


# ── CHART 4: Weekly Spending Line Chart ──────────────────────
def chart_weekly_trend(df: pd.DataFrame, out_dir: str):
    weekly = (
        df.groupby("week")["amount"]
        .sum()
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(
        weekly["week"], weekly["amount"],
        color="#378ADD", linewidth=2.5, marker="o",
        markersize=6, zorder=3
    )
    ax.fill_between(
        weekly["week"], weekly["amount"],
        alpha=0.12, color="#378ADD"
    )
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(rupee))
    ax.set_title("Weekly Spending Trend")
    ax.set_xlabel("Week Number")
    ax.set_ylabel("Amount (₹)")
    ax.grid(linestyle="--", alpha=0.4, zorder=1)

    fig.tight_layout()
    path = os.path.join(out_dir, "chart_04_weekly_trend.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Saved: {path}")


# ── CHART 5: Top 10 Merchants Horizontal Bar ─────────────────
def chart_top_merchants(df: pd.DataFrame, out_dir: str):
    top = (
        df.groupby("description")["amount"]
        .sum()
        .sort_values(ascending=True)
        .tail(10)
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(
        top.index, top.values,
        color="#7F77DD", height=0.6, zorder=2
    )
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(rupee))
    ax.set_title("Top 10 Merchants by Total Spend")
    ax.set_xlabel("Total Spent (₹)")
    ax.grid(axis="x", linestyle="--", alpha=0.4, zorder=1)

    for bar in bars:
        w = bar.get_width()
        ax.text(
            w + 100, bar.get_y() + bar.get_height() / 2,
            f"₹{w:,.0f}",
            va="center", fontsize=8
        )

    fig.tight_layout()
    path = os.path.join(out_dir, "chart_05_top_merchants.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Saved: {path}")


# ── CHART 6: Savings Simulator Bar Chart ─────────────────────
def chart_savings_simulator(df: pd.DataFrame, out_dir: str):
    cuts = {"Food Delivery": 20, "Shopping": 15, "Entertainment": 20}
    months = 3

    monthly_avg = (
        df.groupby(["month", "category"])["amount"]
        .sum()
        .groupby("category")
        .mean()
    )

    categories = list(cuts.keys())
    current = [monthly_avg.get(c, 0) for c in categories]
    after   = [monthly_avg.get(c, 0) * (1 - cuts[c] / 100) for c in categories]
    savings = [(c - a) * months for c, a in zip(current, after)]

    x = np.arange(len(categories))
    w = 0.3

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - w/2, [c * months for c in current], w,
           label="Current (3-month)", color="#D85A30", alpha=0.85, zorder=2)
    ax.bar(x + w/2, [a * months for a in after], w,
           label="After cut (3-month)", color="#1D9E75", alpha=0.85, zorder=2)

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(rupee))
    ax.set_title(
        f"Savings Simulator — 3-Month Projection\n"
        f"Total saving: ₹{sum(savings):,.0f}"
    )
    ax.set_xticks(x)
    labels = [f"{c}\n(-{cuts[c]}%)" for c in categories]
    ax.set_xticklabels(labels)
    ax.set_ylabel("Amount (₹)")
    ax.legend(fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=1)

    fig.tight_layout()
    path = os.path.join(out_dir, "chart_06_savings_simulator.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Saved: {path}")


# ── RUN ALL ──────────────────────────────────────────────────
if __name__ == "__main__":
    base      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base, "outputs", "cleaned_transactions.csv")
    out_dir   = os.path.join(base, "outputs", "charts")

    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(data_path, parse_dates=["date"])

    print("\n🎨 Generating all charts...\n")
    chart_monthly_trend(df, out_dir)
    chart_category_donut(df, out_dir)
    chart_stacked_monthly(df, out_dir)
    chart_weekly_trend(df, out_dir)
    chart_top_merchants(df, out_dir)
    chart_savings_simulator(df, out_dir)
    print("\n✅ All 6 charts saved to outputs/charts/")
