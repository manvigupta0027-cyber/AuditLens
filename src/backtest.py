"""
Backtest: would AuditLens have flagged troubled companies BEFORE their event year?
Needs 'group' (Healthy/Failed/Mid) and 'event_year' in the data (from companies.csv).
A company counts as 'caught' if it was Medium/High risk in any of the 3 years before the event.
"""
import numpy as np
import pandas as pd

FLAG = ["Medium", "High"]


def run(scores: pd.DataFrame, window=3):
    failed = scores[scores["group"] == "Failed"]
    rows = []
    for c, g in failed.groupby("company"):
        ev = g["event_year"].iloc[0]
        if pd.isna(ev):
            continue
        pre = g[(g["year"] < ev) & (g["year"] >= ev - window)].dropna(subset=["risk_score"])
        flagged = pre[pre["risk_tier"].isin(FLAG)]
        rows.append(dict(company=c, event_year=int(ev), years_scored=len(pre),
                         caught=bool(len(flagged)) if len(pre) >= 2 else None,
                         first_flag_year=int(flagged["year"].min()) if len(flagged) else None,
                         lead_time_years=int(ev - flagged["year"].min()) if len(flagged) else None,
                         max_risk_score=pre["risk_score"].max() if len(pre) else None))
    res = pd.DataFrame(rows)

    healthy = scores[(scores["group"] == "Healthy")].dropna(subset=["risk_score"])
    fa = healthy["risk_tier"].isin(FLAG).mean() if len(healthy) else np.nan
    scored = res.dropna(subset=["caught"]) if len(res) else res
    summary = dict(failed_tested=len(scored),
                   failed_caught=int(scored["caught"].sum()) if len(scored) else 0,
                   hit_rate=float(scored["caught"].mean()) if len(scored) else np.nan,
                   avg_lead_time=float(scored["lead_time_years"].mean()) if len(scored) else np.nan,
                   healthy_false_alarm_rate=float(fa))
    return res, summary
