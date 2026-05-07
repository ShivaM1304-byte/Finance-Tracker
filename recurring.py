# ============================================================
# recurring.py  —  Finance Tracker
# Automatically detects recurring payments/subscriptions
# by finding merchants that appear across multiple months.
# ============================================================

import pandas as pd
import os

BASE       = os.path.dirname(os.path.abspath(__file__))
CLEAN_PATH = os.path.join(BASE, "outputs", "cleaned_transactions.csv")

# ── TERMINAL COLORS ──────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def clean_merchant_name(desc: str) -> str:
    """
    Simplify merchant names for grouping.
    'ZOMATO ORDER 1234' and 'ZOMATO ORDER 5678'
    should both be treated as 'ZOMATO'.
    """
    desc = str(desc).upper().strip()

    # Known merchants to normalize
    MERCHANT_MAP = {
        "ZOMATO":      "Zomato",
        "SWIGGY":      "Swiggy",
        "NETFLIX":     "Netflix",
        "HOTSTAR":     "Hotstar / Disney+",
        "SPOTIFY":     "Spotify",
        "AMAZON":      "Amazon",
        "FLIPKART":    "Flipkart",
        "JIO":         "Jio Recharge",
        "AIRTEL":      "Airtel",
        "BSNL":        "BSNL",
        "BESCOM":      "BESCOM Electricity",
        "MSEDCL":      "MSEDCL Electricity",
        "BIGBASKET":   "BigBasket",
        "GOOGLE":      "Google",
        "YOUTUBE":     "YouTube Premium",
        "PRIME":       "Amazon Prime",
        "BOOKMYSHOW":  "BookMyShow",
        "RAPIDO":      "Rapido",
        "UBER":        "Uber",
        "OLA":         "Ola",
    }

    for key, name in MERCHANT_MAP.items():
        if key in desc:
            return name

    # Return first 3 words as merchant name for unknown ones
    words = desc.split()
    return " ".join(words[:3]).title()


def detect_recurring(df: pd.DataFrame,
                     min_months: int = 2,
                     amount_tolerance: float = 0.15) -> pd.DataFrame:
    """
    Find merchants that appear in 2 or more different months.

    min_months        — how many months must it appear in
    amount_tolerance  — how similar the amount must be (15% tolerance)
                        e.g. ₹649 and ₹699 are treated as same subscription
    """

    # ── Normalize merchant names ──────────────────────────────
    df = df.copy()
    df["merchant"] = df["description"].apply(clean_merchant_name)

    # ── Group by merchant and month ───────────────────────────
    grouped = (
        df.groupby(["merchant", "month", "month_name"])["amount"]
        .agg(["sum", "count", "mean"])
        .reset_index()
    )
    grouped.columns = ["merchant", "month", "month_name",
                       "total", "count", "avg_amount"]

    # ── Find merchants appearing in multiple months ───────────
    month_counts = (
        grouped.groupby("merchant")["month"]
        .nunique()
        .reset_index()
        .rename(columns={"month": "months_appeared"})
    )

    # Filter — must appear in at least min_months
    recurring_merchants = month_counts[
        month_counts["months_appeared"] >= min_months
    ]["merchant"].tolist()

    if not recurring_merchants:
        return pd.DataFrame()

    # ── Build recurring summary ───────────────────────────────
    recurring = grouped[grouped["merchant"].isin(recurring_merchants)].copy()

    summary = (
        recurring.groupby("merchant")
        .agg(
            months_appeared=("month", "nunique"),
            avg_monthly_amount=("avg_amount", "mean"),
            total_paid=("total", "sum"),
            months_list=("month_name", lambda x: ", ".join(sorted(set(x))))
        )
        .reset_index()
    )

    # ── Calculate yearly projection ───────────────────────────
    summary["yearly_projection"] = summary["avg_monthly_amount"] * 12

    # Sort by highest monthly amount first
    summary = summary.sort_values("avg_monthly_amount", ascending=False)

    return summary


def categorize_subscription(merchant: str) -> str:
    """Tag each recurring payment with a type."""
    m = merchant.lower()
    if any(k in m for k in ["netflix","hotstar","spotify","prime","youtube","bookmyshow"]):
        return "🎬 Entertainment"
    elif any(k in m for k in ["jio","airtel","bsnl","broadband"]):
        return "📡 Telecom"
    elif any(k in m for k in ["bescom","msedcl","electricity","water","gas"]):
        return "⚡ Utilities"
    elif any(k in m for k in ["zomato","swiggy"]):
        return "🍱 Food Delivery"
    elif any(k in m for k in ["amazon","flipkart","google"]):
        return "🛒 Shopping / Cloud"
    else:
        return "🔄 Other"


def print_report(summary: pd.DataFrame, total_months: int):
    """Print a beautiful recurring payments report."""

    print("\n" + "="*60)
    print(f"{BOLD}  📅 RECURRING PAYMENTS DETECTOR{RESET}")
    print(f"  Analyzed {total_months} months of transaction data")
    print("="*60)

    if summary.empty:
        print(f"\n  {GREEN}✅ No recurring payments detected!{RESET}\n")
        return

    total_yearly = 0

    for _, row in summary.iterrows():
        tag = categorize_subscription(row["merchant"])
        yearly = row["yearly_projection"]
        total_yearly += yearly

        # Color based on yearly cost
        if yearly > 10000:
            color = RED
        elif yearly > 5000:
            color = YELLOW
        else:
            color = GREEN

        print(f"\n  {color}{BOLD}{row['merchant']}{RESET}  {tag}")
        print(f"     Seen in     : {row['months_list']}")
        print(f"     Avg/month   : {CYAN}₹{row['avg_monthly_amount']:,.0f}{RESET}")
        print(f"     Total paid  : ₹{row['total_paid']:,.0f}")
        print(f"     Yearly cost : {color}{BOLD}₹{yearly:,.0f}/year{RESET}")
        print(f"     Appearances : {int(row['months_appeared'])} month(s)")

    # ── TOTALS ────────────────────────────────────────────────
    print("\n" + "-"*60)
    print(f"\n  {BOLD}💸 Total locked in recurring payments:{RESET}")
    print(f"     Per month  : {CYAN}{BOLD}₹{total_yearly/12:,.0f}{RESET}")
    print(f"     Per year   : {RED}{BOLD}₹{total_yearly:,.0f}{RESET}")
    print(f"\n  {YELLOW}💡 Review these payments — cancel what you don't use!{RESET}")
    print("="*60 + "\n")


def run_recurring_check():
    """Main function — loads data, detects, prints report."""

    if not os.path.exists(CLEAN_PATH):
        print(f"\n❌ No cleaned data found.")
        print("   Run  python main.py  first!\n")
        return

    df = pd.read_csv(CLEAN_PATH, parse_dates=["date"])

    total_months = df["month"].nunique()
    print(f"\n🔍 Scanning {len(df)} transactions across "
          f"{total_months} months...")

    summary = detect_recurring(df, min_months=2)
    print_report(summary, total_months)

    # ── Save to CSV ───────────────────────────────────────────
    if not summary.empty:
        out_path = os.path.join(BASE, "outputs", "recurring_payments.csv")
        summary.to_csv(out_path, index=False)
        print(f"  ✅ Saved → {out_path}\n")

    return summary


if __name__ == "__main__":
    run_recurring_check()