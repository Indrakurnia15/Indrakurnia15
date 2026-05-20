#!/usr/bin/env python3
"""Fetch and display analyst estimates for NVDA (NVIDIA Corporation)."""

import yfinance as yf
from datetime import datetime


def get_analyst_estimates(ticker: str) -> None:
    stock = yf.Ticker(ticker)

    print(f"\n{'='*60}")
    print(f"  Analyst Estimates for {ticker} — {datetime.today().strftime('%Y-%m-%d')}")
    print(f"{'='*60}\n")

    info = stock.info

    print("--- Price Target & Recommendation ---")
    print(f"  Current Price       : ${info.get('currentPrice', 'N/A')}")
    print(f"  Target Mean Price   : ${info.get('targetMeanPrice', 'N/A')}")
    print(f"  Target High Price   : ${info.get('targetHighPrice', 'N/A')}")
    print(f"  Target Low Price    : ${info.get('targetLowPrice', 'N/A')}")
    print(f"  Target Median Price : ${info.get('targetMedianPrice', 'N/A')}")
    print(f"  Analyst Count       : {info.get('numberOfAnalystOpinions', 'N/A')}")
    print(f"  Recommendation      : {info.get('recommendationKey', 'N/A').upper()}")
    print(f"  Recommendation Mean : {info.get('recommendationMean', 'N/A')} (1=Strong Buy, 5=Sell)")

    print("\n--- EPS (Earnings Per Share) Estimates ---")
    eps_trend = stock.eps_trend
    if eps_trend is not None and not eps_trend.empty:
        print(eps_trend.to_string())
    else:
        print("  No EPS trend data available.")

    print("\n--- Revenue Estimates ---")
    rev_est = stock.revenue_estimate
    if rev_est is not None and not rev_est.empty:
        print(rev_est.to_string())
    else:
        print("  No revenue estimate data available.")

    print("\n--- EPS Revisions ---")
    eps_rev = stock.eps_revisions
    if eps_rev is not None and not eps_rev.empty:
        print(eps_rev.to_string())
    else:
        print("  No EPS revision data available.")

    print("\n--- Recent Upgrades / Downgrades (last 10) ---")
    upgrades = stock.upgrades_downgrades
    if upgrades is not None and not upgrades.empty:
        print(upgrades.head(10).to_string())
    else:
        print("  No upgrade/downgrade data available.")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    get_analyst_estimates("NVDA")
