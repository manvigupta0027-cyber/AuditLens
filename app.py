import os
import pandas as pd
import plotly.express as px
import streamlit as st
from src.explain import reasons, audit_focus

st.set_page_config(page_title="AuditLens", layout="wide")
st.title("AuditLens")
st.caption("Financial red-flag screening for Indian listed companies - Beneish M, Altman Z'' and Piotroski F, combined into a transparent 0-100 risk score. "
           "A high score means 'look closer', not 'fraud'.")

DATA = "outputs/dashboard_data.csv" if os.path.exists("outputs/dashboard_data.csv") else "outputs/full_scores.csv"
if not os.path.exists(DATA):
    st.error("Run `python run_analysis.py` first."); st.stop()
df = pd.read_csv(DATA)
df["risk_tier"] = pd.Categorical(df["risk_tier"], ["Low", "Medium", "High"], ordered=True)

st.sidebar.header("Filters")
year = st.sidebar.selectbox("Year", sorted(df["year"].unique(), reverse=True))
sectors = st.sidebar.multiselect("Sector", sorted(df["sector"].dropna().unique()))
tiers = st.sidebar.multiselect("Risk tier", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
view = df[(df["year"] == year) & df["risk_tier"].isin(tiers)]
if sectors:
    view = view[view["sector"].isin(sectors)]

t1, t2, t3, t4 = st.tabs(["Risk ranking", "Company drill-down", "Sector view", "Backtest"])

with t1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Companies", len(view))
    c2.metric("High risk", int((view["risk_tier"] == "High").sum()))
    c3.metric("Medium risk", int((view["risk_tier"] == "Medium").sum()))
    cols = ["company", "sector", "risk_score", "risk_tier", "m_score", "z_score", "f_score", "cfo_to_pat"]
    st.dataframe(view.sort_values("risk_score", ascending=False)[cols].round(2), width='stretch', hide_index=True)

with t2:
    company = st.selectbox("Company", sorted(df["company"].unique()))
    cdf = df[df["company"] == company].sort_values("year")
    row = cdf[cdf["year"] == year]
    if len(row) and pd.notna(row.iloc[0]["risk_score"]):
        r = row.iloc[0]
        st.subheader(f"{company} - {year}: {r['risk_tier']} risk ({r['risk_score']:.0f}/100)")
        for x in reasons(r): st.write("- " + x)
        st.info(audit_focus(r))
    else:
        st.warning("No score for this year (needs a prior year for comparison).")
    a, b = st.columns(2)
    a.plotly_chart(px.line(cdf, x="year", y="risk_score", markers=True, title="Risk score over time"), width='stretch')
    b.plotly_chart(px.line(cdf, x="year", y=["m_score"], markers=True, title="Beneish M-Score (above -1.78 = warning)").add_hline(y=-1.78, line_dash="dash"), width='stretch')
    a.plotly_chart(px.line(cdf, x="year", y="z_score", markers=True, title="Altman Z'' (below 1.1 = distress)").add_hline(y=1.1, line_dash="dash"), width='stretch')
    b.plotly_chart(px.line(cdf, x="year", y="cfo_to_pat", markers=True, title="Cash conversion: operating cash flow / net profit (below 0.5 = weak)").add_hline(y=0.5, line_dash="dash"), width='stretch')

with t3:
    sec = df[df["year"] == year].groupby("sector")["risk_score"].mean().sort_values(ascending=False).reset_index()
    st.plotly_chart(px.bar(sec, x="sector", y="risk_score", title=f"Average risk score by sector, {year}"), width='stretch')

with t4:
    if os.path.exists("outputs/backtest_results.csv"):
        s = pd.read_csv("outputs/backtest_summary.csv", index_col=0)["value"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Failed companies caught", f"{int(s['failed_caught'])} / {int(s['failed_tested'])}")
        c2.metric("Avg. early warning (years)", f"{s['avg_lead_time']:.1f}")
        c3.metric("False-alarm rate (healthy)", f"{s['healthy_false_alarm_rate']:.0%}")
        st.dataframe(pd.read_csv("outputs/backtest_results.csv"), width='stretch', hide_index=True)
        st.caption("Caught = rated Medium/High in any of the 3 years before the failure year.")
    else:
        st.info("Backtest appears once real data with a 'Failed' group is loaded.")
