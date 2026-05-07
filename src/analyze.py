# ============================================================
# analyze.py  —  Finance Tracker
# Step 2: Time-series analysis — monthly trends, category
#         breakdowns, weekly patterns, savings simulation
# ============================================================

import pandas as pd
import os


def load_cleaned(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, parse_dates=["date"])
    return df


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Total spending per month, per category.
    Returns a pivot table: rows = months, columns = categories.
    """
    summary = (
        df.groupby(["month", "month_name", "category"])["amount"]
        .sum()
        .reset_index()
    )

    pivot = summary.pivot_table(
        index=["month", "month_name"],
        columns="category",
        values="amount",
        fill_value=0
    )

    pivot = pivot.sort_index(level="month")
    pivot["TOTAL"] = pivot.sum(axis=1)

    return pivot


def top_merchants(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Which merchants cost you the most money overall?
    """
    top = (
        df.groupby("description")["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
    )
    top.columns = ["merchant", "total_spent"]
    return top


def weekly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Total spending per week number.
    Useful for spotting binge-spending weeks.
    """
    weekly = (
        df.groupby("week")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "weekly_total"})
    )
    return weekly


def category_share(df: pd.DataFrame) -> pd.DataFrame:
    """
    Percentage share of each category in total spend.
    """
    total = df["amount"].sum()
    share = (
        df.groupby("category")["amount"]
        .sum()
        .reset_index()
    )
    share["percentage"] = (share["amount"] / total * 100).round(1)
    share = share.sort_values("percentage", ascending=False)
    return share


def savings_simulator(
    df: pd.DataFrame,
    cuts: dict,
    months: int = 3
) -> dict:
    """
    If you cut spending in certain categories by given percentages,
    how much do you save?

    cuts = {"Food Delivery": 20, "Shopping": 10, "Entertainment": 15}
    months = how many months to project into the future
    """
    # average monthly spend per category
    monthly_avg = (
        df.groupby(["month", "category"])["amount"]
        .sum()
        .groupby("category")
        .mean()
    )

    results = {}
    total_monthly_saving = 0

    for category, cut_pct in cuts.items():
        if category in monthly_avg.index:
            avg = monthly_avg[category]
            saving = avg * (cut_pct / 100)
            results[category] = {
                "avg_monthly_spend": round(avg, 2),
                "cut_percent": cut_pct,
                "monthly_saving": round(saving, 2),
                f"{months}_month_saving": round(saving * months, 2),
            }
            total_monthly_saving += saving

    results["TOTAL"] = {
        "monthly_saving": round(total_monthly_saving, 2),
        f"{months}_month_saving": round(total_monthly_saving * months, 2),
        "annual_projection": round(total_monthly_saving * 12, 2),
    }

    return results


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cleaned_path = os.path.join(base, "outputs", "cleaned_transactions.csv")

    df = load_cleaned(cleaned_path)

    print("\n" + "="*55)
    print("📅  MONTHLY SUMMARY (₹)")
    print("="*55)
    monthly = monthly_summary(df)
    print(monthly.to_string())

    print("\n" + "="*55)
    print("🏪  TOP 10 MERCHANTS BY SPEND")
    print("="*55)
    print(top_merchants(df).to_string(index=False))

    print("\n" + "="*55)
    print("📊  CATEGORY SHARE")
    print("="*55)
    print(category_share(df).to_string(index=False))

    print("\n" + "="*55)
    print("💰  SAVINGS SIMULATOR (3 months)")
    print("="*55)
    cuts = {"Food Delivery": 20, "Shopping": 15, "Entertainment": 20}
    sim = savings_simulator(df, cuts, months=3)
    for cat, vals in sim.items():
        print(f"\n  {cat}:")
        for k, v in vals.items():
            print(f"    {k}: ₹{v:,.0f}")

    # Save monthly summary
    out = os.path.join(base, "outputs", "monthly_summary.csv")
    monthly.to_csv(out)
    print(f"\n✅ Monthly summary saved → {out}")
