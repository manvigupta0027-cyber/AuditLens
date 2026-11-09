"""Creates DUMMY data (with planted problems) to test the pipeline. Replace with real data later."""
import numpy as np, pandas as pd
rng = np.random.default_rng(42)

def company(name, sector, kind, years=range(2018, 2025)):
    rows, sales, dd, borrow, reserves = [], 1000.0, 55.0, 150.0, 400.0
    for i, y in enumerate(years):
        late = i >= 4
        g = rng.uniform(0.06, 0.12)
        if kind == "manipulator" and late: g = rng.uniform(0.30, 0.40)    # sales jump...
        if kind == "distressed" and late: g = rng.uniform(-0.12, -0.04)
        sales *= 1 + g
        if kind == "manipulator" and late: dd *= 1.35                      # ...receivables balloon
        else: dd *= rng.uniform(0.98, 1.02)
        margin = rng.uniform(0.16, 0.20) - (0.05 * (i - 3) if kind == "distressed" and late else 0)
        expenses = sales * (1 - margin)
        dep = sales * 0.03
        np_ = (sales - expenses - dep) * 0.65
        if kind == "distressed" and late: borrow *= 1.4
        reserves += np_ * (0.9 if kind != "distressed" or not late else 0.2)
        cfo = np_ * rng.uniform(0.9, 1.2)
        if kind == "manipulator" and late: cfo = np_ * rng.uniform(-0.1, 0.3)
        fixed = sales * 0.45; cwip = sales * 0.03; inv = sales * 0.05
        eq_cap = 100.0
        other_liab = sales * 0.18
        total_assets = eq_cap + reserves + borrow + other_liab
        other_assets = total_assets - fixed - cwip - inv
        rows.append(dict(company=name, sector=sector, year=y, sales=sales, expenses=expenses,
            depreciation=dep, other_income=sales * 0.01, net_profit=np_, equity_capital=eq_cap,
            reserves=reserves, borrowings=borrow, total_assets=total_assets, fixed_assets=fixed,
            cwip=cwip, investments=inv, other_assets=other_assets, other_liabilities=other_liab,
            cfo=cfo, debtor_days=dd))
    return rows

plan = [("Alpha Industries","Manufacturing","normal"),("Beta Pharma","Pharma","normal"),
        ("Gamma Retail","Retail","normal"),("Delta Auto","Auto","normal"),
        ("Epsilon Infra","Infra","manipulator"),("Zeta Textiles","Textiles","manipulator"),
        ("Eta Power","Power","distressed"),("Theta Realty","Realty","distressed"),
        ("Iota IT","IT","normal"),("Kappa FMCG","FMCG","normal")]
df = pd.DataFrame([r for n, s, k in plan for r in company(n, s, k)])
df.round(2).to_csv("data/sample_data.csv", index=False)
print("rows:", len(df))
