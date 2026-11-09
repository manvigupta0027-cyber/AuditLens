# AuditLens

**Live demo:** https://auditlens-avmkvq6w9rw9t6mmhrm9ia.streamlit.app/

Data-driven screening of Indian listed companies for earnings manipulation and financial distress
# AuditLens

**Financial Red-Flag Screening for Indian Listed Companies**

**Live demo:** https://auditlens-avmkvq6w9rw9t6mmhrm9ia.streamlit.app/

AuditLens combines three forensic accounting models (Beneish M-Score, Altman Z''-Score and Piotroski F-Score) into one transparent 0-100 risk score. Every flag comes with plain-English reasons and a suggested audit focus, so an auditor knows where to look first.

## Business question

Auditors cannot test every company in depth. Which companies deserve the closest look, and why?

## What it does

- Loads 10 years of financials per company from Screener.in exports.
- Scores each company-year with Beneish M (earnings manipulation), Altman Z'' (distress risk) and Piotroski F (financial health), plus trend checks on receivables vs sales and profit vs operating cash flow.
- Combines the signals into a 0-100 risk score (Low / Medium / High) where every point comes from a named rule.
- Explains each flag in plain English and suggests what to audit first.
- Backtests the score against companies that went into insolvency.
- Serves everything in an interactive Streamlit dashboard: risk ranking, company drill-down, sector view and backtest.

## Backtest (small sample: an early indication, not proof)

Data: 12 Indian listed companies (6 healthy, 6 troubled), about 10 years each. Failure year is the financial year of the first NCLT insolvency admission. A company counts as "caught" if it was rated Medium or High in any of the 3 years before failure.

| Company | Failure FY | First flag | Early warning | Max score |
|---|---|---|---|---|
| Jet Airways | 2020 | 2017 | 3 years | 70 (High) |
| Amtek Auto | 2018 | 2016 | 2 years | 40 (Medium) |
| Videocon Industries | 2019 | 2018 | 1 year | 35 (Medium) |

- All 3 testable failures were flagged.
(Beneish M-Score, Altman Z''-Score, Piotroski F-Score -> transparent 0-100 risk score), backtested on known failures.


## Run it
1. Download each company's Excel from screener.in (Export to Excel) into `data/raw/`,
   named exactly as in the `file` column of `data/companies.csv` (e.g. `asian_paints.xlsx`).
2. `python -m src.loader`        -> builds data/real_data.csv + outputs/data_quality_report.csv
3. `python run_analysis.py`      -> scores, ranking, backtest (outputs/)
4. `streamlit run app.py`        -> dashboard

Without real data, steps 3-4 run on the dummy `data/sample_data.csv`.

## Known limitations (state these openly)
- Beneish/Altman/Piotroski were built on US data; thresholds may differ for India.
- A high score means "look closer", not "fraud".
- Banks/NBFCs/insurers excluded (different balance sheets).
- Screener has no separate COGS, so operating margin proxies gross margin; asset-quality and working-capital are proxies.
- Backtest sample is small and limited to companies whose history is still available (survivorship bias).
