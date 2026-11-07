"""Calculate returns, rolling statistics, and efficient frontiers for Homework 1."""

from __future__ import annotations

import hashlib
import itertools
import json
import platform
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
TICKERS = ["AAPL", "XOM", "PFE", "ED"]
PAIRS = list(itertools.combinations(TICKERS, 2))
START, END = "2024-10-01", "2026-10-01"
WINDOW, DAYS, MONTHS = 30, 252, 12
OUT, FIG, TAB = ROOT / "results", ROOT / "figures", ROOT / "report" / "tables"
for directory in [OUT, FIG, TAB]:
    directory.mkdir(parents=True, exist_ok=True)


def save_table(frame, name, *, percent=False, digits=2):
    formatter = (lambda x: f"{100*x:.{digits}f}\\%") if percent else (lambda x: f"{x:.{digits}f}")
    text = frame.to_latex(escape=False, float_format=formatter, na_rep="--")
    (TAB / f"{name}.tex").write_text(text, encoding="utf-8")


def save_figure(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def portfolio(mu, cov, target=None, long_only=True):
    """Find minimum-variance weights by checking each subset of stocks."""
    n = len(mu)
    candidates = []
    supports = (range(n),) if not long_only else (
        s for k in range(1, n + 1) for s in itertools.combinations(range(n), k)
    )
    for support in supports:
        ids = list(support)
        subcov = cov[np.ix_(ids, ids)]
        if target is not None and len(ids) == 1:
            if not np.isclose(mu[ids[0]], target, atol=1e-11, rtol=0):
                continue
            subweights = np.ones(1)
        else:
            constraints = np.ones((1, len(ids)))
            rhs = np.ones(1)
            if target is not None:
                constraints = np.vstack([constraints, mu[ids]])
                rhs = np.array([1.0, target])
            inv_a = np.linalg.solve(subcov, constraints.T)
            try:
                subweights = inv_a @ np.linalg.solve(constraints @ inv_a, rhs)
            except np.linalg.LinAlgError:
                continue
        if long_only and np.min(subweights) < -1e-9:
            continue
        weights = np.zeros(n)
        weights[ids] = subweights
        if abs(weights.sum() - 1) > 1e-8:
            continue
        if target is not None and abs(weights @ mu - target) > 1e-8:
            continue
        candidates.append((weights @ cov @ weights, weights))
    if not candidates:
        raise ValueError(f"No feasible portfolio at target {target}")
    return min(candidates, key=lambda item: item[0])[1]


def main():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": .18, "axes.axisbelow": True,
        "savefig.facecolor": "white", "pdf.fonttype": 42,
    })
    colors = dict(zip(TICKERS, ["#2166ac", "#b35806", "#7b3294", "#18806b"]))
    series, indices, provenance = [], [], {}
    for ticker in TICKERS:
        path = ROOT / "data" / "raw" / f"{ticker}.csv"
        frame = pd.read_csv(path)
        frame.index = pd.DatetimeIndex(pd.to_datetime(frame.pop("Date").str[:10]), name="Date")
        assert frame.index.is_unique and frame.index.is_monotonic_increasing
        assert frame.index.min() == pd.Timestamp("2024-09-30")
        assert frame.index.max() == pd.Timestamp(END)
        assert frame["Adj Close"].notna().all() and (frame["Adj Close"] > 0).all()
        series.append(frame["Adj Close"].rename(ticker))
        indices.append(frame.index)
        provenance[ticker] = {"source_url": f"https://finance.yahoo.com/quote/{ticker}/history/",
                              "raw_file": str(path.relative_to(ROOT)).replace("\\", "/"),
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                              "price_observations": len(frame),
                              "first_date": str(frame.index.min().date()),
                              "last_date": str(frame.index.max().date()),
                              "last_close": float(frame["Close"].iloc[-1])}
    # All four stocks should have the same trading dates.
    assert all(index.equals(indices[0]) for index in indices)
    prices = pd.concat(series, axis=1)
    assert not prices.isna().any().any()
    daily = prices.pct_change(fill_method=None).loc[START:END]
    assert daily.index.min() == pd.Timestamp(START) and daily.index.max() == pd.Timestamp(END)
    assert not daily.isna().any().any()
    rolling_vol = daily.rolling(WINDOW, min_periods=WINDOW).std(ddof=1).dropna() * np.sqrt(DAYS)
    rolling_corr = pd.DataFrame({
        f"{a}--{b}": daily[a].rolling(WINDOW, min_periods=WINDOW).corr(daily[b])
        for a, b in PAIRS
    }).dropna()
    assert len(rolling_vol) == len(rolling_corr) == len(daily) - WINDOW + 1
    assert rolling_corr.abs().to_numpy().max() <= 1 + 1e-12
    assert (rolling_vol >= 0).all().all()

    # Exclude the incomplete October 2026 month.
    monthly_prices = prices.loc[:"2026-09-30"].resample("ME").last()
    monthly = monthly_prices.pct_change(fill_method=None).dropna()
    assert len(monthly) == 24
    assert monthly.index.min() == pd.Timestamp("2024-10-31")
    assert monthly.index.max() == pd.Timestamp("2026-09-30")
    compounded = (1 + daily.loc[:"2026-09-30"]).resample("ME").prod() - 1
    np.testing.assert_allclose(compounded, monthly, rtol=1e-10, atol=1e-12)
    monthly_cov, monthly_corr = monthly.cov(ddof=1), monthly.corr()
    mu, cov = monthly.mean().to_numpy() * MONTHS, monthly_cov.to_numpy() * MONTHS
    np.testing.assert_allclose(monthly_corr, monthly_corr.T, atol=1e-12)
    np.testing.assert_allclose(np.diag(monthly_corr), 1, atol=1e-12)
    assert np.linalg.eigvalsh(cov).min() > 0
    np.testing.assert_allclose(np.outer(np.sqrt(np.diag(cov)), np.sqrt(np.diag(cov))) * monthly_corr, cov)
    gmv = portfolio(mu, cov)
    targets = np.linspace(gmv @ mu, mu.max(), 201)
    weights = np.vstack([portfolio(mu, cov, target) for target in targets])
    risks = np.sqrt(np.einsum("ij,jk,ik->i", weights, cov, weights))
    np.testing.assert_allclose(weights.sum(axis=1), 1, atol=1e-9)
    np.testing.assert_allclose(weights @ mu, targets, atol=1e-9)
    assert weights.min() > -1e-9 and np.diff(risks).min() > -1e-9
    equal = np.ones(4) / 4
    assert gmv @ cov @ gmv <= min(np.diag(cov).min(), equal @ cov @ equal) + 1e-10

    # Compare a few frontier points with SLSQP.
    max_solver_gap = 0.0
    for i in [0, 20, 60, 100, 140, 180]:
        target = targets[i]
        initial = equal if i == 0 else weights[i-1]
        constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
        if i != 0:
            constraints.append({"type": "eq", "fun": lambda w, t=target: w @ mu - t})
        result = minimize(lambda w: w @ cov @ w, initial, jac=lambda w: 2 * cov @ w,
                          constraints=constraints, bounds=[(0, 1)] * 4,
                          method="SLSQP", options={"ftol": 1e-13, "maxiter": 1000})
        assert result.success, result.message
        gap = abs(result.fun - weights[i] @ cov @ weights[i])
        max_solver_gap = max(max_solver_gap, gap)
        assert gap < 1e-8

    un_gmv = portfolio(mu, cov, long_only=False)
    un_targets = np.linspace(un_gmv @ mu, mu.max(), 201)
    un_weights = np.vstack([portfolio(mu, cov, target, long_only=False) for target in un_targets])
    un_risks = np.sqrt(np.einsum("ij,jk,ik->i", un_weights, cov, un_weights))

    daily_summary = pd.DataFrame({
        "Mean daily": daily.mean(), "Daily std.": daily.std(ddof=1),
        "Annualized vol.": daily.std(ddof=1) * np.sqrt(DAYS),
        "Cumulative return": (1 + daily).prod() - 1,
    })
    vol_summary = rolling_vol.agg(["mean", "std", "min", "median", "max"]).T
    corr_summary = rolling_corr.agg(["mean", "std", "min", "median", "max"]).T
    monthly_summary = pd.DataFrame({
        "Monthly mean": monthly.mean(), "Monthly vol.": monthly.std(ddof=1),
        "Annual mean": mu, "Annual vol.": np.sqrt(np.diag(cov)),
    }, index=TICKERS)
    frontier = pd.DataFrame(weights, columns=TICKERS)
    frontier.insert(0, "annual_volatility", risks)
    frontier.insert(0, "annual_expected_return", targets)
    un_frontier = pd.DataFrame(un_weights, columns=TICKERS)
    un_frontier.insert(0, "annual_volatility", un_risks)
    un_frontier.insert(0, "annual_expected_return", un_targets)
    selected = {}
    for label, w in [("Minimum variance", gmv), ("Equal weight", equal),
                     ("Midpoint target", weights[100]), ("Maximum mean", weights[-1])]:
        selected[label] = [*w, w @ mu, np.sqrt(w @ cov @ w)]
    selected = pd.DataFrame.from_dict(selected, orient="index", columns=TICKERS + ["Annual mean", "Annual vol."])

    exports = {"adjusted_prices": prices, "daily_returns": daily,
               "rolling_30d_annualized_volatility": rolling_vol,
               "rolling_30d_correlations": rolling_corr,
               "monthly_prices": monthly_prices, "monthly_returns": monthly,
               "daily_summary": daily_summary, "rolling_volatility_summary": vol_summary,
               "rolling_correlation_summary": corr_summary,
               "monthly_summary": monthly_summary, "monthly_covariance": monthly_cov,
               "monthly_correlation": monthly_corr,
               "annualized_monthly_covariance": pd.DataFrame(cov, index=TICKERS, columns=TICKERS),
               "efficient_frontier_long_only": frontier,
               "efficient_frontier_unconstrained": un_frontier,
               "selected_portfolios": selected}
    for name, frame in exports.items():
        frame.to_csv(OUT / f"{name}.csv", float_format="%.12g")
    with pd.ExcelWriter(OUT / "homework1_calculations.xlsx", engine="openpyxl") as writer:
        for name, frame in exports.items():
            frame.to_excel(writer, sheet_name=name[:31])

    save_table(daily_summary, "daily_summary", percent=True)
    preview = pd.concat([daily.head(3), daily.tail(3)])
    preview.index = preview.index.strftime("%Y-%m-%d")
    save_table(preview, "daily_preview", percent=True, digits=4)
    save_table(vol_summary, "rolling_volatility_summary", percent=True)
    corr_summary.index = corr_summary.index.str.replace("--", " / ", regex=False)
    save_table(corr_summary, "rolling_correlation_summary", digits=3)
    save_table(monthly_summary, "monthly_summary", percent=True)
    save_table(monthly_corr, "monthly_correlation", digits=4)
    save_table(monthly_cov, "monthly_covariance", digits=6)
    save_table(selected, "selected_portfolios", percent=True)

    fig, axes = plt.subplots(4, 1, figsize=(10.0, 8.0), sharex=True, layout="constrained")
    for ax, ticker in zip(axes, TICKERS):
        ax.plot(daily.index, daily[ticker], color=colors[ticker], linewidth=.65)
        ax.axhline(0, color="gray", linewidth=.5)
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.set_ylabel(ticker)
    axes[0].set_title("Daily adjusted-close returns | October 1, 2024 - October 1, 2026", loc="left")
    save_figure(fig, "daily_returns")

    fig, axes = plt.subplots(2, 2, figsize=(10, 6.8), sharex=True, sharey=True, layout="constrained")
    bins = np.linspace(0, float(rolling_vol.to_numpy().max()) * 1.03, 26)
    for ax, ticker in zip(axes.flat, TICKERS):
        values = rolling_vol[ticker]
        ax.hist(values, bins=bins, color=colors[ticker], alpha=.85, edgecolor="white", linewidth=.4)
        ax.axvline(values.mean(), color="#333333", linestyle="--", linewidth=1.1, label=f"Mean {values.mean():.1%}")
        ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        ax.set(title=ticker, xlabel="Annualized volatility", ylabel="Number of windows")
        ax.legend(frameon=False, fontsize=9)
    save_figure(fig, "volatility_histograms")

    fig, axes = plt.subplots(3, 2, figsize=(10, 8.2), sharex=True, sharey=True, layout="constrained")
    for ax, (a, b) in zip(axes.flat, PAIRS):
        values = rolling_corr[f"{a}--{b}"]
        ax.hist(values, bins=np.linspace(-1, 1, 26), color="#427b91", alpha=.85, edgecolor="white", linewidth=.4)
        ax.axvline(values.mean(), color="#333333", linestyle="--", linewidth=1.1, label=f"Mean {values.mean():.3f}")
        ax.set(title=f"{a} / {b}", xlabel="Pearson correlation", ylabel="Number of windows", xlim=(-1, 1))
        ax.legend(frameon=False, fontsize=9)
    save_figure(fig, "correlation_histograms")

    rng = np.random.default_rng(6991)
    random_w = rng.dirichlet(np.ones(4), size=12000)
    random_returns = random_w @ mu
    random_risks = np.sqrt(np.einsum("ij,jk,ik->i", random_w, cov, random_w))
    fig, ax = plt.subplots(figsize=(10, 6.4), layout="constrained")
    ax.scatter(random_risks, random_returns, s=3, alpha=.13, color="#84a9b8", label="Feasible long-only portfolios", rasterized=True)
    ax.plot(un_risks, un_targets, color="#a56524", linestyle="--", linewidth=1.6, label="Efficient frontier: short selling allowed")
    ax.plot(risks, targets, color="#173e63", linewidth=2.6, label="Efficient frontier: long only")
    for j, ticker in enumerate(TICKERS):
        ax.scatter(np.sqrt(cov[j, j]), mu[j], color=colors[ticker], s=65, zorder=5)
        ax.annotate(ticker, (np.sqrt(cov[j, j]), mu[j]), xytext=(7, 5), textcoords="offset points", fontweight="bold", color=colors[ticker])
    ax.scatter(np.sqrt(gmv @ cov @ gmv), gmv @ mu, marker="*", s=210, color="#b83c35", zorder=6, label="Long-only minimum variance")
    ax.scatter(np.sqrt(equal @ cov @ equal), equal @ mu, marker="D", s=50, color="#333333", zorder=5, label="Equal weight")
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set(xlabel="Annualized volatility from monthly returns", ylabel="Annualized arithmetic expected return",
           title="Mean-variance efficient frontier | 24 complete monthly observations")
    ax.margins(x=.12, y=.15)
    ax.legend(frameon=True, fontsize=8.5, loc="best")
    save_figure(fig, "efficient_frontier")

    summary = {
        "author": "Panagiotis Housos", "course": "Asset Allocation (FRE 6991), Fall 2026",
        "sample": {"daily_start": START, "daily_end": END, "daily_observations": len(daily),
                   "price_observations_with_baseline": len(prices), "rolling_window": WINDOW,
                   "rolling_observations": len(rolling_vol),
                   "first_window_end": str(rolling_vol.index.min().date()),
                   "monthly_observations": len(monthly), "monthly_start": "2024-10", "monthly_end": "2026-09"},
        "annualization": {"trading_days": DAYS, "months": MONTHS, "std_ddof": 1},
        "gmv": {"weights": dict(zip(TICKERS, gmv)), "annual_mean": float(gmv @ mu),
                "annual_volatility": float(np.sqrt(gmv @ cov @ gmv))},
        "validation": {"passed": True, "same_trading_dates_all_stocks": True,
                       "missing_prices": 0, "dropped_dates": 0, "forward_filled_prices": 0,
                       "monthly_compounding_matches_daily": True,
                       "covariance_min_eigenvalue": float(np.linalg.eigvalsh(cov).min()),
                       "independent_optimizer_max_variance_gap": max_solver_gap},
        "raw_data_provenance": provenance,
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "pandas": pd.__version__, "matplotlib": matplotlib.__version__},
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("\nMONTHLY STATISTICS\n", monthly_summary.to_string())
    print("\nSELECTED PORTFOLIOS\n", selected.to_string())


if __name__ == "__main__":
    main()
