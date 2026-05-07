# ============================================================
# budget.py  —  Finance Tracker
# Set monthly budget limits per category.
# Compares your actual spending vs your limits.
# Prints a color-coded report in the terminal.
# ============================================================

import pandas as pd
import os

BASE       = os.path.dirname(os.path.abspath(__file__))
CLEAN_PATH = os.path.join(BASE, "outputs", "cleaned_transactions.csv")

# ── YOUR MONTHLY BUDGET LIMITS ────────────────────────────────
# Change these numbers to whatever you want your limit to be!
# These are in Indian Rupees (₹)

BUDGETS = {
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

# ── TERMINAL COLORS ──────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def get_monthly_spending(df: pd.DataFrame, month: int) -> dict:
    """Get total spending per category for a given month number."""
    month_df = df[df["month"] == month]
    result   = month_df.groupby("category")["amount"].sum().to_dict()
    return result


def check_budget(spending: dict, budgets: dict) -> list:
    """
    Compare actual spending vs budget for each category.
    Returns a list of result dictionaries.
    """
    results = []

    for category, limit in budgets.items():
        spent   = spending.get(category, 0)
        pct     = (spent / limit * 100) if limit > 0 else 0
        remaining = limit - spent

        if pct >= 100:
            status = "OVER BUDGET"
            color  = RED
        elif pct >= 80:
            status = "WARNING"
            color  = YELLOW
        else:
            status = "SAFE"
            color  = GREEN

        results.append({
            "category":  category,
            "spent":     spent,
            "limit":     limit,
            "pct":       pct,
            "remaining": remaining,
            "status":    status,
            "color":     color,
        })

    # Sort — over budget first, then warning, then safe
    order = {"OVER BUDGET": 0, "WARNING": 1, "SAFE": 2}
    results.sort(key=lambda x: order[x["status"]])

    return results


def print_report(results: list, month_name: str,
                 total_spent: float, total_budget: float):
    """Print a beautiful color-coded budget report."""

    print("\n" + "="*58)
    print(f"{BOLD}  💰 BUDGET REPORT — {month_name.upper()}{RESET}")
    print("="*58)

    for r in results:
        # Build progress bar
        filled = int(min(r["pct"], 100) / 5)   # max 20 blocks
        bar    = "█" * filled + "░" * (20 - filled)

        # Status emoji
        emoji = "✅" if r["status"] == "SAFE" else \
                "⚠️ " if r["status"] == "WARNING" else "🚨"

        print(
            f"\n  {emoji} {r['color']}{BOLD}{r['category']:<18}{RESET}"
            f"\n     [{bar}] {r['pct']:.0f}%"
            f"\n     Spent: ₹{r['spent']:>7,.0f}  /  "
            f"Budget: ₹{r['limit']:>7,.0f}  |  "
            f"{'Over by' if r['remaining']<0 else 'Remaining'}: "
            f"₹{abs(r['remaining']):,.0f}  "
            f"{r['color']}({r['status']}){RESET}"
        )

    # ── TOTALS ────────────────────────────────────────────────
    total_pct  = (total_spent / total_budget * 100) if total_budget else 0
    over_count = sum(1 for r in results if r["status"] == "OVER BUDGET")
    warn_count = sum(1 for r in results if r["status"] == "WARNING")

    print("\n" + "-"*58)
    print(f"  {BOLD}Total Budget : ₹{total_budget:>8,.0f}{RESET}")
    print(f"  {BOLD}Total Spent  : ₹{total_spent:>8,.0f}{RESET}  "
          f"({total_pct:.1f}% of budget)")

    if over_count:
        print(f"\n  {RED}{BOLD}🚨 {over_count} categor"
              f"{'y' if over_count==1 else 'ies'} over budget!{RESET}")
    if warn_count:
        print(f"  {YELLOW}⚠️  {warn_count} categor"
              f"{'y' if warn_count==1 else 'ies'} approaching limit!{RESET}")
    if not over_count and not warn_count:
        print(f"\n  {GREEN}{BOLD}🎉 Great job! All categories within budget!{RESET}")

    print("="*58 + "\n")


def run_budget_check(month: int = None):
    """
    Main function — loads data, checks budget, prints report.
    If month is None, checks the most recent month in the data.
    """
    # ── Load cleaned data ─────────────────────────────────────
    if not os.path.exists(CLEAN_PATH):
        print(f"\n❌ No cleaned data found at {CLEAN_PATH}")
        print("   Run  python main.py  first!\n")
        return

    df = pd.read_csv(CLEAN_PATH, parse_dates=["date"])

    # ── Pick month ────────────────────────────────────────────
    if month is None:
        month = int(df["month"].max())   # most recent month

    month_name = df[df["month"] == month]["month_name"].iloc[0] \
                 if len(df[df["month"] == month]) > 0 else f"Month {month}"

    # ── Check ─────────────────────────────────────────────────
    spending     = get_monthly_spending(df, month)
    results      = check_budget(spending, BUDGETS)
    total_spent  = sum(r["spent"]  for r in results)
    total_budget = sum(r["limit"]  for r in results)

    print_report(results, month_name, total_spent, total_budget)

    # ── Also show all available months ───────────────────────
    available = df[["month","month_name"]].drop_duplicates() \
                  .sort_values("month")
    print(f"  💡 Tip: Check a specific month by editing budget.py")
    print(f"     Available months in your data:")
    for _, row in available.iterrows():
        marker = " ← currently showing" if row["month"]==month else ""
        print(f"       Month {int(row['month'])}: {row['month_name']}{marker}")
    print()

    return results


if __name__ == "__main__":
    run_budget_check()