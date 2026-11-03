"""Explicitly refresh Yahoo Finance inputs; analyze.py uses saved inputs offline."""

from datetime import datetime
from importlib.metadata import version
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import yfinance as yf

root = Path(__file__).resolve().parents[1]
out = root / "data" / "raw"
out.mkdir(parents=True, exist_ok=True)
for ticker in ["AAPL", "XOM", "PFE", "ED"]:
    data = yf.Ticker(ticker).history(start="2024-09-30", end="2026-10-02", auto_adjust=False, actions=True)
    if data.empty or "Adj Close" not in data:
        raise ValueError(f"Missing adjusted-close data for {ticker}")
    data.to_csv(out / f"{ticker}.csv", index_label="Date")
    print(f"Saved {ticker}: {len(data)} prices")
metadata = {
    "retrieved_at": datetime.now(ZoneInfo("America/New_York")).isoformat(),
    "provider": "Yahoo Finance via yfinance", "yfinance_version": version("yfinance"),
    "request": {"start_inclusive": "2024-09-30", "end_exclusive": "2026-10-02", "auto_adjust": False, "actions": True},
    "note": "The 2024-09-30 price supplies the first requested daily return; October 2026 is incomplete for monthly analysis.",
}
(out / "download_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
