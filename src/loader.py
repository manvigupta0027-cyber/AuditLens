"""
Reads Screener.in 'Export to Excel' files (sheet 'Data Sheet') in data/raw/
and builds data/real_data.csv in the format scores.py expects.
Company metadata (group, sector, event_year) comes from data/companies.csv.
"""
import glob, os
import numpy as np
import pandas as pd
from openpyxl import load_workbook

SECTIONS = {"PROFIT & LOSS": "pl", "BALANCE SHEET": "bs", "CASH FLOW": "cf"}
STOP = {"PRICE", "DERIVED", "QUARTERS", "META"}
EXPENSE_ROWS = ["Raw Material Cost", "Change in Inventory", "Power and Fuel",
                "Other Mfr. Exp", "Employee Cost", "Selling and admin", "Other Expenses"]


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def _fy(d):
    """Indian FY ends in March: 31-Mar-2024 -> FY2024."""
    return d.year if d.month <= 6 else d.year + 1


def parse_file(path):
    wb = load_workbook(path, data_only=True)
    ws = wb["Data Sheet"] if "Data Sheet" in wb.sheetnames else wb.worksheets[0]
    sec, data, dates, totals = None, {"pl": {}, "bs": {}, "cf": {}}, {}, []
    for r in ws.iter_rows(values_only=True):
        if r[0] is None:
            continue
        lab = str(r[0]).strip()
        up = lab.upper().rstrip(":")
        if up in SECTIONS:
            sec = SECTIONS[up]; continue
        if up in STOP:
            sec = None; continue
        if sec is None:
            continue
        vals = list(r[1:])
        if lab == "Report Date":
            dates[sec] = vals
        elif lab == "Total" and sec == "bs":
            totals.append(vals)
        else:
            data[sec][lab] = vals

    pl_dates = dates.get("pl", [])
    rows = []
    for i, d in enumerate(pl_dates):
        if d is None or not hasattr(d, "year"):
            continue
        g = lambda s, l: _num(data[s].get(l, [np.nan] * (i + 1))[i]) if i < len(data[s].get(l, [])) else np.nan
        exp = sum(0 if np.isnan(g("pl", l)) else g("pl", l) for l in EXPENSE_ROWS)
        sales = g("pl", "Sales")
        # Robust operating-expense identity: operating profit = PBT + interest + depreciation - other income.
        # Avoids sign problems in Screener's 'Change in Inventory' row.
        _pbt, _int, _dep, _oi = (g("pl", "Profit before tax"), g("pl", "Interest"),
                                 g("pl", "Depreciation"), g("pl", "Other Income"))
        if not (np.isnan(_pbt) or np.isnan(_int) or np.isnan(_dep) or np.isnan(sales)):
            exp = sales - (_pbt + _int + _dep - (0 if np.isnan(_oi) else _oi))
        recv = g("bs", "Receivables")
        ta = _num(totals[1][i]) if len(totals) > 1 and i < len(totals[1]) else np.nan
        rows.append(dict(
            year=_fy(d), sales=sales, expenses=exp,
            depreciation=g("pl", "Depreciation"), other_income=g("pl", "Other Income"),
            net_profit=g("pl", "Net profit"),
            equity_capital=g("bs", "Equity Share Capital"), reserves=g("bs", "Reserves"),
            borrowings=g("bs", "Borrowings"), other_liabilities=g("bs", "Other Liabilities"),
            total_assets=ta, fixed_assets=g("bs", "Net Block"),
            cwip=g("bs", "Capital Work in Progress"), investments=g("bs", "Investments"),
            other_assets=g("bs", "Other Assets"), cfo=g("cf", "Cash from Operating Activity"),
            debtor_days=recv / sales * 365 if sales and not np.isnan(recv) else np.nan))
    return pd.DataFrame(rows)


def build(raw_dir="data/raw", meta_path="data/companies.csv", out="data/real_data.csv"):
    meta = pd.read_csv(meta_path) if os.path.exists(meta_path) else pd.DataFrame(columns=["file"])
    meta["file"] = meta["file"].astype(str)
    frames, report = [], []
    for f in sorted(glob.glob(os.path.join(raw_dir, "*.xlsx"))):
        stem = os.path.splitext(os.path.basename(f))[0]
        try:
            df = parse_file(f)
        except Exception as e:
            report.append((stem, "ERROR", str(e))); continue
        m = meta[meta["file"] == stem]
        df["company"] = m["company"].iloc[0] if len(m) else stem
        df["sector"] = m["sector"].iloc[0] if len(m) else "Unknown"
        df["group"] = m["group"].iloc[0] if len(m) else "Unknown"
        df["event_year"] = m["event_year"].iloc[0] if len(m) else np.nan
        df = df.dropna(subset=["sales"])
        miss = df[["net_profit", "total_assets", "cfo", "debtor_days"]].isna().any(axis=1).sum()
        status = "OK" if len(df) >= 6 and miss == 0 else "CHECK"
        report.append((stem, status, f"{len(df)} years, {miss} years with missing key fields"))
        frames.append(df)
    if not frames:
        raise SystemExit("No .xlsx files found in data/raw/")
    out_df = pd.concat(frames, ignore_index=True)
    out_df.to_csv(out, index=False)
    pd.DataFrame(report, columns=["file", "status", "note"]).to_csv("outputs/data_quality_report.csv", index=False)
    for r in report:
        print(f"{r[1]:6} {r[0]:25} {r[2]}")
    print(f"\nSaved {len(out_df)} rows for {out_df['company'].nunique()} companies -> {out}")
    return out_df


if __name__ == "__main__":
    build()
