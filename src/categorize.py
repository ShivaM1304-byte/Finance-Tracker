# ============================================================
# categorize.py  —  Finance Tracker
# Step 1: Load raw data, clean it, assign categories
# ============================================================

import pandas as pd
import os

# ── CATEGORIZATION RULES ─────────────────────────────────────
# Each category has a list of keywords.
# We search for these keywords inside the transaction description.
# The FIRST match wins. "Others" is the fallback.

CATEGORY_RULES = {
    "Food Delivery": [
        "zomato", "swiggy", "dunzo", "magicpin", "eatsure"
    ],
    "Groceries": [
        "bigbasket", "dmart", "reliance fresh", "grofers",
        "blinkit", "zepto", "grocery"
    ],
    "Transport": [
        "ola", "uber", "rapido", "namma metro", "metro",
        "irctc", "redbus"
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "nykaa", "ajio",
        "meesho", "snapdeal", "retail", "purchase", "fashion"
    ],
    "Utilities": [
        "bescom", "msedcl", "electricity", "jio", "airtel",
        "bsnl", "broadband", "recharge", "water"
    ],
    "Entertainment": [
        "bookmyshow", "pvr", "inox", "netflix", "hotstar",
        "spotify", "prime video", "cinemas", "ticket",
        "subscription"
    ],
    "Health": [
        "apollo", "medplus", "fortis", "manipal",
        "pharmacy", "hospital", "clinic", "medical"
    ],
    "Rent": [
        "rent", "housing", "maintenance", "society"
    ],
    "Income": [
        "salary", "credit", "cashback", "refund"
    ],
}


def categorize(description: str) -> str:
    """
    Given a transaction description string,
    return the matching category name.
    """
    desc_lower = description.lower()

    for category, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if kw in desc_lower:
                return category

    return "Others"  # fallback if nothing matches


def load_and_clean(filepath: str) -> pd.DataFrame:
    """
    Load the CSV, clean it, add useful columns.
    Returns a clean DataFrame.
    """

    # ── 1. LOAD ──────────────────────────────────────────────
    df = pd.read_csv(filepath)
    print(f"✅ Loaded {len(df)} rows from {filepath}")

    # ── 2. CLEAN ─────────────────────────────────────────────
    # Convert date column to proper datetime type
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")

    # Remove rows with zero or missing amounts
    df = df[df["amount"] > 0].copy()
    print(f"✅ After removing zero-amount rows: {len(df)} rows")

    # Strip whitespace from description
    df["description"] = df["description"].str.strip()

    # ── 3. SEPARATE DEBITS AND CREDITS ───────────────────────
    debits = df[df["type"] == "debit"].copy()
    credits = df[df["type"] == "credit"].copy()
    print(f"✅ Debits (expenses): {len(debits)} | Credits (income): {len(credits)}")

    # ── 4. CATEGORIZE ────────────────────────────────────────
    debits["category"] = debits["description"].apply(categorize)

    # ── 5. ADD TIME COLUMNS ──────────────────────────────────
    debits["month"] = debits["date"].dt.month          # 1, 2, 3 ...
    debits["month_name"] = debits["date"].dt.strftime("%B")  # January ...
    debits["week"] = debits["date"].dt.isocalendar().week.astype(int)
    debits["day_of_week"] = debits["date"].dt.day_name()

    print(f"\n📊 Category distribution:")
    print(debits["category"].value_counts().to_string())

    return debits, credits


if __name__ == "__main__":
    # Paths
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = os.path.join(base, "data", "transactions.csv")
    out_path = os.path.join(base, "outputs", "cleaned_transactions.csv")

    debits, credits = load_and_clean(filepath)

    # Save cleaned data
    debits.to_csv(out_path, index=False)
    print(f"\n✅ Cleaned data saved → {out_path}")