"""Turns score columns into plain-English reasons an auditor can act on."""
import pandas as pd


def reasons(r) -> list:
    out = []
    if pd.notna(r.get("m_score")) and r["m_score"] > -1.78:
        out.append(f"Beneish M-Score {r['m_score']:.2f} is above the -1.78 warning line (possible earnings manipulation).")
    elif pd.notna(r.get("m_score")) and r["m_score"] > -2.22:
        out.append(f"Beneish M-Score {r['m_score']:.2f} is in the grey zone (-2.22 to -1.78).")
    if pd.notna(r.get("rec_growth")) and r.get("rec_pts", 0) > 0:
        out.append(f"Receivables grew {r['rec_growth']:.0%} while sales grew {r['sales_growth']:.0%} - customers may be paying slower or sales may be aggressive.")
    if r.get("cash_pts", 0) > 0:
        ratio = r.get("cfo_to_pat")
        txt = f"only {ratio:.0%} of profit converted to operating cash" if pd.notna(ratio) else "operating cash flow is negative despite profit"
        out.append(f"Profit is not backed by cash: {txt}.")
    if pd.notna(r.get("z_score")) and r["z_score"] < 2.6:
        zone = "distress" if r["z_score"] < 1.1 else "grey"
        out.append(f"Altman Z'' {r['z_score']:.2f} is in the {zone} zone (bankruptcy risk).")
    if pd.notna(r.get("f_score")) and r["f_score"] <= 5:
        out.append(f"Piotroski F-Score {int(r['f_score'])}/9 - business fundamentals are {'weak' if r['f_score'] <= 3 else 'mediocre'}.")
    return out or ["No major red flags in this year."]


def audit_focus(r) -> str:
    areas = []
    if r.get("rec_pts", 0) > 0 or (pd.notna(r.get("m_score")) and r["m_score"] > -1.78):
        areas.append("revenue recognition and receivable ageing / customer confirmations")
    if r.get("cash_pts", 0) > 0:
        areas.append("quality of earnings (reconcile profit to operating cash flow)")
    if pd.notna(r.get("z_score")) and r["z_score"] < 2.6:
        areas.append("going-concern assessment, debt covenants and refinancing risk")
    return "Prioritise: " + "; ".join(areas) + "." if areas else "Routine procedures."
