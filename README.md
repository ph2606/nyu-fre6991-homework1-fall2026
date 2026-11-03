# Homework 1 — Volatility & Correlation

**Panagiotis Housos · ph2606**<br>
**New York University · Asset Allocation (FRE 6991) · Fall 2026**<br>
Prepared November 3, 2026 · Due Sunday, November 8, 2026

The completed report answers the supplied assignment for **AAPL, XOM, PFE, and ED**.

- [Compiled report (PDF)](report/homework1_report.pdf)
- [LaTeX source](report/homework1_report.tex)
- [Calculation workbook](results/homework1_calculations.xlsx)
- [All 502 daily returns](results/daily_returns.csv)
- [Original assignment](assignment/HW1_VOLATILITY%20AND%20CORRELATION1.docx)

## Methods and coverage

Daily simple returns use Yahoo Finance's split- and dividend-adjusted closing prices. The frozen inputs contain 503 prices, including the September 30, 2024 baseline. There are **502 daily returns dated October 1, 2024 through October 1, 2026 inclusive**, with no missing prices, dropped dates, or forward filling.

A window is **30 trading-return observations**. Annualized volatility is sample standard deviation (`ddof=1`) times `sqrt(252)`. The four volatility histograms and six unique Pearson-correlation histograms each use **473 overlapping windows**. Correlations are not annualized.

Monthly returns use the **24 complete calendar months from October 2024 through September 2026**. October 1, 2026 remains in the daily analysis but is excluded from monthly estimates because it is an incomplete month. Monthly arithmetic means and covariance are multiplied by 12 for the annualized frontier; monthly volatility is multiplied by `sqrt(12)`.

The main frontier assumes full investment and nonnegative weights. A supplemental short-sales frontier is shown over the same displayed return range. Both are optimized curves, not an envelope inferred from random portfolios. With four assets, the code solves the long-only quadratic program by enumerating all 15 possible nonzero weight supports. Random portfolios are displayed only as context. No risk-free rate or tangency portfolio is assumed.

## Selected results

The long-only minimum-variance weights are **33.05% AAPL, 0.00% XOM, 19.76% PFE, and 47.19% ED**. Based on monthly observations, the estimated annual arithmetic return is **10.15%** and annualized volatility is **9.59%**. The equal-weight portfolio has an estimated annual arithmetic return of **13.65%** and volatility of **11.59%**. These are historical sample estimates.

## Reproduce

Python 3.12 and the pinned packages in `requirements.txt` were used. A TeX distribution providing `pdflatex` is required to rebuild the report.

```powershell
python -m pip install -r requirements.txt
python scripts/analyze.py
python scripts/build_report.py --skip-analysis
```

Or run `python scripts/build_report.py` to perform both steps. The saved data allow analysis and report generation without fetching market data. For an explicit data refresh, run `python scripts/download_data.py`, then rebuild. A refresh may incorporate vendor revisions and change estimates.

The report's written numerical discussion reflects the committed data snapshot. If inputs change, review that discussion after regenerating tables and figures.

## Files

| Location | Contents |
|---|---|
| `assignment/` | Original instructor-supplied Word assignment and extracted text |
| `data/raw/` | Four frozen Yahoo price histories and download metadata |
| `scripts/analyze.py` | Calculations, exact frontier solver, validation, tables, workbook, and figures |
| `scripts/download_data.py` | Optional explicit refresh of the four input histories |
| `scripts/build_report.py` | Two-pass LaTeX compilation, optionally preceded by analysis |
| `results/` | Full daily/monthly returns, rolling estimates, matrices, portfolio weights, workbook, and validation summary |
| `figures/` | Publication-quality PDF charts and PNG previews |
| `report/` | LaTeX source, generated tables, and compiled PDF |

CSV and workbook returns, volatility, covariance, and weights are stored in **decimal units**. Report return and volatility tables use percentages; correlations are dimensionless; covariance is in squared decimal monthly-return units. `results/summary.json` records input SHA-256 hashes, sample counts, software versions, and validation results.

## Validation

Checks cover matching observed trading dates, valid input prices, daily sample boundaries, rolling window counts, 24 monthly observations, monthly compounding against daily returns, correlation properties, covariance positive definiteness, and portfolio feasibility. An independent SLSQP optimizer verifies six points on the exact long-only frontier; the maximum variance difference was below `1e-8`. Sample size and overlapping-window limitations are discussed in the report.

## Data sources

Yahoo Finance historical data: [AAPL](https://finance.yahoo.com/quote/AAPL/history/), [XOM](https://finance.yahoo.com/quote/XOM/history/), [PFE](https://finance.yahoo.com/quote/PFE/history/), and [ED](https://finance.yahoo.com/quote/ED/history/), retrieved November 3, 2026 via `yfinance`. Yahoo documents split and dividend adjustments in [What is the adjusted close?](https://in.help.yahoo.com/kb/adjusted-close-sln28256.html).
