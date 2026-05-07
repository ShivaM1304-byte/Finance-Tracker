# ============================================================
# load_real_data.py  —  Finance Tracker
# Reads YOUR real Kotak Bank CSV statement,
# cleans it, and converts it to the same format
# that the rest of the project understands.
# ============================================================

import pandas as pd
import re
import os

BASE     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")

# ── CHANGE THIS to your actual downloaded filename ───────────
BANK_CSV = os.path.join(DATA_DIR, "kotak_statement.csv")
OUT_CSV  = os.path.join(DATA_DIR, "transactions.csv")


# ── SMART CATEGORIZER for real UPI descriptions ──────────────
CATEGORY_RULES = {
    "Food Delivery": [
        "zomato", "swiggy", "dunzo", "magicpin", "eatsure",
        "blinkit food", "zepto food"
    ],
    "Groceries": [
        "bigbasket", "dmart", "reliance fresh", "blinkit",
        "zepto", "grofers", "grocery", "vegetables", "kirana",
        "supermarket", "nature basket"
    ],
    "Transport": [
        "ola", "uber", "rapido", "namma metro", "metro",
        "irctc", "redbus", "makemytrip", "ease my trip",
        "petrol", "fuel", "parking"
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "nykaa", "ajio",
        "meesho", "snapdeal", "retail", "fashion", "mall",
        "powerlook", "max fashion", "westside", "shoppers"
    ],
    "Utilities": [
        "bescom", "msedcl", "electricity", "jio", "airtel",
        "bsnl", "broadband", "recharge", "water", "gas",
        "mahanagar", "tata power", "adani electric"
    ],
    "Entertainment": [
        "bookmyshow", "pvr", "inox", "netflix", "hotstar",
        "spotify", "prime", "cinemas", "ticket", "youtube",
        "google india"   # Google One / Play subscriptions
    ],
    "Health": [
        "apollo", "medplus", "fortis", "manipal",
        "pharmacy", "hospital", "clinic", "medical",
        "netmeds", "1mg", "pharmeasy"
    ],
    "Food & Dining": [
        "restaurant", "hotel", "cafe", "dhaba", "biryani",
        "pizza", "burger", "canteen", "bakery", "cakes",
        "batulz", "annapurna", "caterers", "mess"
    ],
    "Rent": [
        "rent", "housing", "maintenance", "society", "pg "
    ],
    "Transfer Out": [
        "neft", "imps", "rtgs"
    ],
}


def categorize(description: str) -> str:
    desc = description.lower()
    for category, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if kw in desc:
                return category
    return "Others"


def extract_upi_merchant(description: str) -> str:
    """
    Kotak UPI descriptions look like:
      UPI/MERCHANT NAME/ref/note
    Extract just the merchant name part.
    """
    desc = description.strip()

    # Pattern: UPI/MERCHANT NAME/numbers/...
    match = re.match(r"UPI[/_]([^/]+)/", desc, re.IGNORECASE)
    if match:
        name = match.group(1).strip().title()
        return name

    # For non-UPI entries, return cleaned description
    return desc[:40]


def clean_amount(val) -> float:
    """Remove commas from amounts like '2,670.00' → 2670.0"""
    if pd.isna(val):
        return 0.0
    return float(str(val).replace(",", "").strip())


def load_kotak_csv(filepath: str) -> pd.DataFrame:
    """
    Kotak statements have address/account info at the top
    before the actual transaction table starts.
    We skip those rows automatically.
    """
    print(f"📂 Reading: {filepath}")

    # ── Find which row the actual headers are on ─────────────
    header_row = None
    with open(filepath, "r", encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if "Transaction Date" in line or "Sl. No." in line:
                header_row = i
                break

    if header_row is None:
        raise ValueError(
            "Could not find 'Transaction Date' header in your CSV.\n"
            "Make sure you downloaded the correct Kotak statement."
        )

    print(f"✅ Found transaction headers at row {header_row}")

    # ── Load only from the header row onwards ────────────────
    df = pd.read_csv(filepath, skiprows=header_row, encoding="utf-8-sig")

    print(f"✅ Loaded {len(df)} raw rows")
    print(f"   Columns found: {list(df.columns)}")

    return df


def process(df: pd.DataFrame) -> tuple:
    """
    Clean, convert, and categorize the raw bank DataFrame.
    Returns (debits, credits) as separate DataFrames.
    """

    # ── Rename columns to standard names ─────────────────────
    df = df.rename(columns={
        "Transaction Date": "raw_date",
        "Description":      "raw_description",
        "Amount":           "amount",
        "Dr / Cr":          "type",
        "Balance":          "balance",
    })

    # ── Drop rows with missing date or amount ─────────────────
    df = df.dropna(subset=["raw_date", "amount"])

    # ── Parse date (Kotak format: DD-MM-YYYY HH:MM:SS) ───────
    df["date"] = pd.to_datetime(
        df["raw_date"].str[:10],   # take only DD-MM-YYYY part
        format="%d-%m-%Y",
        errors="coerce"
    )
    df = df.dropna(subset=["date"])

    # ── Clean amount (remove commas) ─────────────────────────
    df["amount"] = df["amount"].apply(clean_amount)
    df = df[df["amount"] > 0]

    # ── Standardize type: DR → debit, CR → credit ────────────
    df["type"] = df["type"].str.strip().str.upper()
    df["type"] = df["type"].map({"DR": "debit", "CR": "credit"})
    df = df.dropna(subset=["type"])

    # ── Extract clean merchant name from UPI description ──────
    df["description"] = df["raw_description"].apply(extract_upi_merchant)

    # ── Add time columns ─────────────────────────────────────
    df["month"]      = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%B")
    df["week"]       = df["date"].dt.isocalendar().week.astype(int)
    df["day_of_week"]= df["date"].dt.day_name()

    # ── Split debits and credits ──────────────────────────────
    debits  = df[df["type"] == "debit"].copy()
    credits = df[df["type"] == "credit"].copy()

    # ── Categorize debits ─────────────────────────────────────
    debits["category"] = debits["raw_description"].apply(categorize)

    print(f"\n✅ Debits (expenses): {len(debits)}")
    print(f"✅ Credits (income) : {len(credits)}")
    print(f"\n📊 Category distribution:")
    print(debits["category"].value_counts().to_string())

    # ── Save in standard format ───────────────────────────────
    keep_cols = ["date","description","amount","type",
                 "category","month","month_name","week","day_of_week"]
    debits_out = debits[keep_cols].copy()

    return debits_out, credits


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  Finance Tracker — Real Bank Data Loader")
    print("="*55)

    # ── Check file exists ─────────────────────────────────────
    if not os.path.exists(BANK_CSV):
        print(f"\n❌ File not found: {BANK_CSV}")
        print("\n👉 Steps to fix:")
        print(f"   1. Rename your downloaded Kotak CSV to:  kotak_statement.csv")
        print(f"   2. Put it in your:  FINANCE_TRACKER\\data\\  folder")
        print(f"   3. Run this script again\n")
        exit(1)

    raw_df          = load_kotak_csv(BANK_CSV)
    debits, credits = process(raw_df)

    # ── Save cleaned file ─────────────────────────────────────
    debits.to_csv(OUT_CSV, index=False)
    print(f"\n✅ Saved cleaned data → {OUT_CSV}")

    # ── Summary ───────────────────────────────────────────────
    print(f"\n📅 Date range: {debits['date'].min().date()} → {debits['date'].max().date()}")
    print(f"💸 Total spent: ₹{debits['amount'].sum():,.0f}")
    print(f"📦 Months covered: {debits['month_name'].nunique()}")

    print("\n" + "="*55)
    print("  ✅ Done! Now run:")
    print("     python main.py")
    print("     python dashboard.py")
    print("  to see YOUR real spending data!")
    print("="*55 + "\n")