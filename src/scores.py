"""
Forensic scoring models for Indian listed companies.
Input: one row per company-year (columns follow Screener.in's layout).
Models: Beneish M-Score, Altman Z''-Score, Piotroski F-Score + combined risk score.
NOTE: Screener.in has no COGS / SG&A / current-asset split, so a few inputs are
approximations. They are documented below and should be mentioned in the interview.
"""
import numpy as np
import pandas as pd

REQUIRED = ["company", "sector", "year", "sales", "expenses", "depreciation",
            "other_income", "net_profit", "equity_capital", "reserves",
            "borrowings", "total_assets", "fixed_assets", "cwip", "investments",
            "other_assets", "other_liabilities", "cfo", "debtor_days"]


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    df = df.sort_values(["company", "year"]).reset_index(drop=True).copy()
    df["receivables"] = df["debtor_days"] * df["sales"] / 365
    df["equity"] = df["equity_capital"] + df["reserves"]
    df["total_liab"] = df["total_assets"] - df["equity"]
    df["op_profit"] = df["sales"] - df["expenses"]
    df["ebit"] = df["op_profit"] - df["depreciation"] + df["other_income"]
    df["gross_margin"] = df["op_profit"] / df["sales"]   # proxy: operating margin
    return df


def _lag(df, col):
    return df.groupby("company")[col].shift(1)


def beneish(df: pd.DataFrame) -> pd.DataFrame:
    """8-variable Beneish M-Score. Flag if M > -1.78 (conservative cut-off: -2.22)."""
    d = df.copy()
    ta = d["total_assets"]
    ta_l = _lag(d, "total_assets")
    rec, rec_l = d["receivables"], _lag(d, "receivables")
    s, s_l = d["sales"], _lag(d, "sales")

    d["DSRI"] = (rec / s) / (rec_l / s_l)
    d["GMI"] = _lag(d, "gross_margin") / d["gross_margin"]
    # AQI proxy: share of assets that is neither fixed assets nor 'other assets'
    aq = (d["cwip"] + d["investments"]) / ta
    d["AQI"] = aq / ((_lag(d, "cwip") + _lag(d, "investments")) / ta_l)
    d["SGI"] = s / s_l
    dep, dep_l = d["depreciation"], _lag(d, "depreciation")
    ppe, ppe_l = d["fixed_assets"], _lag(d, "fixed_assets")
    d["DEPI"] = (dep_l / (dep_l + ppe_l)) / (dep / (dep + ppe))
    d["SGAI"] = 1.0  # SG&A not available on Screener -> neutral value
    d["TATA"] = (d["net_profit"] - d["cfo"]) / ta
    d["LVGI"] = (d["total_liab"] / ta) / (_lag(d, "total_liab") / ta_l)

    # Winsorise: when a company collapses (sales/equity ~ 0) ratios explode. Cap them so one
    # extreme ratio cannot dominate the score (Beneish himself winsorised his sample).
    for c in ["DSRI", "GMI", "AQI", "SGI", "DEPI", "LVGI"]:
        d[c] = d[c].clip(0, 5)
    d["TATA"] = d["TATA"].clip(-1, 1)
    d["m_score"] = (-4.84 + 0.920 * d["DSRI"] + 0.528 * d["GMI"] + 0.404 * d["AQI"]
                    + 0.892 * d["SGI"] + 0.115 * d["DEPI"] - 0.172 * d["SGAI"]
                    + 4.679 * d["TATA"] - 0.327 * d["LVGI"])
    return d.replace([np.inf, -np.inf], np.nan)


def altman(df: pd.DataFrame) -> pd.DataFrame:
    """Altman Z''-Score (non-manufacturers / emerging markets; uses book equity).
    Safe > 2.6 | Grey 1.1-2.6 | Distress < 1.1"""
    d = df.copy()
    ta = d["total_assets"]
    wc = d["other_assets"] - d["other_liabilities"]   # proxy for working capital
    d["z_score"] = (6.56 * wc / ta + 3.26 * d["reserves"] / ta
                    + 6.72 * d["ebit"] / ta + 1.05 * d["equity"] / d["total_liab"])
    d["z_zone"] = pd.cut(d["z_score"], [-np.inf, 1.1, 2.6, np.inf],
                         labels=["Distress", "Grey", "Safe"])
    return d.replace([np.inf, -np.inf], np.nan)


def piotroski(df: pd.DataFrame) -> pd.DataFrame:
    """9-point F-Score. 8-9 strong, 0-3 weak. (Liquidity uses other_assets/other_liabilities.)"""
    d = df.copy()
    ta = d["total_assets"]
    d["roa"] = d["net_profit"] / ta
    d["lev"] = d["borrowings"] / ta
    d["liq"] = d["other_assets"] / d["other_liabilities"]
    d["turn"] = d["sales"] / ta
    chk = pd.DataFrame({
        "f1_roa_pos": d["roa"] > 0,
        "f2_cfo_pos": d["cfo"] > 0,
        "f3_roa_up": d["roa"] > _lag(d, "roa"),
        "f4_cfo_gt_ni": d["cfo"] > d["net_profit"],
        "f5_lev_down": d["lev"] < _lag(d, "lev"),
        "f6_liq_up": d["liq"] > _lag(d, "liq"),
        "f7_no_dilution": d["equity_capital"] <= _lag(d, "equity_capital"),
        "f8_margin_up": d["gross_margin"] > _lag(d, "gross_margin"),
        "f9_turn_up": d["turn"] > _lag(d, "turn"),
    })
    d["f_score"] = chk.sum(axis=1).astype(float)
    d.loc[_lag(d, "sales").isna(), "f_score"] = np.nan   # first year has no comparison
    return d


def trend_flags(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["rec_growth"] = d["receivables"] / _lag(d, "receivables") - 1
    d["sales_growth"] = d["sales"] / _lag(d, "sales") - 1
    d["cfo_to_pat"] = np.where(d["net_profit"] > 0, d["cfo"] / d["net_profit"], np.nan)
    return d.replace([np.inf, -np.inf], np.nan)


def risk_score(d: pd.DataFrame) -> pd.DataFrame:
    """Transparent 0-100 points system. Every point is explainable to an auditor."""
    d = d.copy()
    pts = pd.DataFrame(index=d.index)
    pts["m_pts"] = np.select([d["m_score"] > -1.78, d["m_score"] > -2.22], [30, 15], 0)
    pts["z_pts"] = np.select([d["z_score"] < 1.1, d["z_score"] < 2.6], [30, 15], 0)
    pts["f_pts"] = np.select([d["f_score"] <= 3, d["f_score"] <= 5], [20, 10], 0)
    pts["cash_pts"] = np.where((d["cfo_to_pat"] < 0.5) | ((d["net_profit"] > 0) & (d["cfo"] < 0)), 10, 0)
    pts["rec_pts"] = np.where((d["rec_growth"] > 0.20) &
                              (d["rec_growth"] > 1.5 * d["sales_growth"].clip(lower=0.01)), 10, 0)
    d = pd.concat([d, pts], axis=1)
    d["risk_score"] = pts.sum(axis=1).astype(float)
    d["risk_tier"] = pd.cut(d["risk_score"], [-1, 29, 59, 100], labels=["Low", "Medium", "High"])
    d.loc[d["m_score"].isna(), ["risk_score", "risk_tier"]] = np.nan  # no prior year -> can't score
    return d


def run_all(raw: pd.DataFrame) -> pd.DataFrame:
    d = prepare(raw)
    d = beneish(d)
    d = altman(d)
    d = piotroski(d)
    d = trend_flags(d)
    return risk_score(d)
