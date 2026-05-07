import os, sys
BASE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(BASE, "src")
sys.path.insert(0, SRC)
from categorize import load_and_clean
from analyze    import monthly_summary, category_share, savings_simulator
from visualize  import (chart_monthly_trend, chart_category_donut,
                        chart_stacked_monthly, chart_weekly_trend,
                        chart_top_merchants, chart_savings_simulator)
def run():
    print("\n" + "="*60)
    print("  FINANCE TRACKER - Personal Spending Analytics")
    print("="*60)
    data_path    = os.path.join(BASE, "data", "transactions.csv")
    outputs_dir  = os.path.join(BASE, "outputs")
    charts_dir   = os.path.join(outputs_dir, "charts")
    cleaned_path = os.path.join(outputs_dir, "cleaned_transactions.csv")
    summary_path = os.path.join(outputs_dir, "monthly_summary.csv")
    os.makedirs(charts_dir, exist_ok=True)
    print("\n[1/3] Cleaning & categorizing transactions...")
    debits, credits = load_and_clean(data_path)
    debits.to_csv(cleaned_path, index=False)
    print("\n[2/3] Running analysis...")
    monthly = monthly_summary(debits)
    monthly.to_csv(summary_path)
    for (month_num, month_name), row in monthly.iterrows():
        print(f"         {month_name}: Rs.{row['TOTAL']:,.0f}")
    share = category_share(debits)
    for _, row in share.iterrows():
        print(f"         {row['category']:<18} {row['percentage']:>5}%  Rs.{row['amount']:,.0f}")
    cuts = {"Food Delivery": 20, "Shopping": 15, "Entertainment": 20}
    sim  = savings_simulator(debits, cuts, months=3)
    t    = sim["TOTAL"]
    print(f"\n      Monthly saving:  Rs.{t['monthly_saving']:,.0f}")
    print(f"      3-month saving: Rs.{t['3_month_saving']:,.0f}")
    print(f"      Annual saving:  Rs.{t['annual_projection']:,.0f}")
    print("\n[3/3] Generating charts...")
    chart_monthly_trend(debits, charts_dir)
    chart_category_donut(debits, charts_dir)
    chart_stacked_monthly(debits, charts_dir)
    chart_weekly_trend(debits, charts_dir)
    chart_top_merchants(debits, charts_dir)
    chart_savings_simulator(debits, charts_dir)
    print("\n  DONE! Check outputs/charts/ for your 6 charts!")
if __name__ == "__main__":
    run()
