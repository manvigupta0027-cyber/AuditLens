# AuditLens

**Live demo:** https://auditlens-avmkvq6w9rw9t6mmhrm9ia.streamlit.app/

Data-driven screening of Indian listed companies for earnings manipulation and financial distress
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
