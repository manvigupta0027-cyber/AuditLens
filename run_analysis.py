import os, sys
import pandas as pd
from src.scores import run_all
from src.backtest import run as backtest

path = sys.argv[1] if len(sys.argv) > 1 else ("data/real_data.csv" if os.path.exists("data/real_data.csv") else "data/sample_data.csv")
print("Using data:", path)
df = pd.read_csv(path)
res = run_all(df)
res.to_csv("outputs/full_scores.csv", index=False)
keep = ["company", "sector", "group", "year", "risk_score", "risk_tier", "m_score", "z_score", "z_zone",
        "f_score", "cfo_to_pat", "rec_growth", "sales_growth", "m_pts", "z_pts", "f_pts", "cash_pts", "rec_pts"]
res[[c for c in keep if c in res.columns]].to_csv("outputs/dashboard_data.csv", index=False)

latest = res[res["year"] == res["year"].max()]
cols = ["company", "sector", "m_score", "z_score", "z_zone", "f_score", "cfo_to_pat", "risk_score", "risk_tier"]
rank = latest[cols].sort_values("risk_score", ascending=False).round(2)
rank.to_csv("outputs/risk_ranking.csv", index=False)
print(rank.to_string(index=False))

if "group" in res.columns and (res["group"] == "Failed").any():
    bt, s = backtest(res)
    bt.to_csv("outputs/backtest_results.csv", index=False)
    pd.Series(s).to_csv("outputs/backtest_summary.csv", header=["value"])
    print("\nBACKTEST:", s)
    print(bt.to_string(index=False))
