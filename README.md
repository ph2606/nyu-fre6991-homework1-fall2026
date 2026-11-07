# Homework 1: Volatility & Correlation

**Panagiotis Housos | ph2606**<br>
NYU Tandon School of Engineering<br>
Asset Allocation (FRE 6991), Fall 2026

Daily returns, rolling volatility and correlations, and the monthly-return efficient frontier for AAPL, XOM, PFE, and ED.

- [Report (PDF)](report/homework1_report.pdf)
- [LaTeX source](report/homework1_report.tex)
- [Calculation workbook](results/homework1_calculations.xlsx)
- [Daily returns (CSV)](results/daily_returns.csv)
- [Assignment](assignment/HW1_VOLATILITY%20AND%20CORRELATION1.docx)

Daily simple returns use split- and dividend-adjusted closing prices from Yahoo Finance. The September 30, 2024 price supplies the baseline for **502 daily returns from October 1, 2024 through October 1, 2026**.

Each rolling estimate uses 30 trading-day returns, giving **473 overlapping windows** per stock or pair. Volatility is the sample standard deviation (`ddof=1`) multiplied by `sqrt(252)`. The report includes four volatility histograms and six pairwise Pearson-correlation histograms. Correlations are not annualized, and the overlapping windows are not independent observations.

Monthly returns use the **24 complete months from October 2024 through September 2026**. The partial October 2026 month is excluded. Monthly arithmetic means and sample covariance are multiplied by 12 for the frontier; monthly volatility is multiplied by `sqrt(12)`.

The main frontier requires weights to sum to one and prohibits short sales. A second curve permits short sales. The long-only minimum-variance portfolio holds **33.05% AAPL, 0% XOM, 19.76% PFE, and 47.19% ED**, with an estimated annual arithmetic return of **10.15%** and volatility of **9.59%**. These estimates come from the 24-month sample and can change with the period used. No risk-free rate is assumed.

To rerun the calculations and build the PDF, use Python 3.12 and a TeX installation with `pdflatex`:

```powershell
python -m pip install -r requirements.txt
python scripts/build_report.py
```

The script reads the saved CSVs. To compile the report without rerunning calculations, add `--skip-analysis`.

CSV and workbook returns, volatilities, and weights use decimals. Covariance uses squared decimal returns; correlations are dimensionless. The report displays returns, volatility, and weights as percentages.

Sources: Yahoo Finance histories for [AAPL](https://finance.yahoo.com/quote/AAPL/history/), [XOM](https://finance.yahoo.com/quote/XOM/history/), [PFE](https://finance.yahoo.com/quote/PFE/history/), and [ED](https://finance.yahoo.com/quote/ED/history/), downloaded through `yfinance`. See Yahoo's [adjusted-close explanation](https://in.help.yahoo.com/kb/adjusted-close-sln28256.html).
