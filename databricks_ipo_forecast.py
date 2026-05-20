"""
Databricks Post-IPO Stock Forecasting
======================================
Uses IPO analogs (SNOW, MDB, CFLT, HCP, ESTC) to simulate Databricks price history
and forecast future performance using Prophet, ARIMA, and Linear Regression.

Simulated Databricks IPO: $220/share on 2026-01-15 (ticker: DBRX)
Analysis date: 2026-05-20
"""

import os
import warnings
import logging

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import yfinance as yf
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet

warnings.filterwarnings("ignore")
logging.getLogger("prophet").setLevel(logging.ERROR)
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)

np.random.seed(42)

# ── Configuration ─────────────────────────────────────────────────────────────
CHARTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

IPO_DATE = datetime(2026, 1, 15)
IPO_PRICE = 220.0
ANALYSIS_DATE = datetime(2026, 5, 20)
TICKER = "DBRX"

COMPS = {
    "SNOW": {"name": "Snowflake",   "ipo_date": "2020-09-16", "ipo_price": 120.0},
    "MDB":  {"name": "MongoDB",     "ipo_date": "2017-10-19", "ipo_price": 24.0},
    "CFLT": {"name": "Confluent",   "ipo_date": "2021-06-24", "ipo_price": 36.0},
    "HCP":  {"name": "HashiCorp",   "ipo_date": "2021-12-09", "ipo_price": 80.0},
    "ESTC": {"name": "Elastic",     "ipo_date": "2018-10-05", "ipo_price": 36.0},
}

FORECAST_DAYS_SHORT = 90
FORECAST_DAYS_LONG  = 180

# ── Styling ───────────────────────────────────────────────────────────────────
PALETTE = {
    "primary":   "#E31837",
    "secondary": "#FF6B35",
    "accent":    "#1A1A2E",
    "grid":      "#EEEEEE",
    "prophet":   "#2196F3",
    "arima":     "#4CAF50",
    "linreg":    "#FF9800",
}

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.grid":        True,
    "grid.color":       PALETTE["grid"],
    "grid.linewidth":   0.6,
    "font.family":      "DejaVu Sans",
    "axes.spines.top":  False,
    "axes.spines.right": False,
})


# ══════════════════════════════════════════════════════════════════════════════
# 1.  COMP DATA — fetch real historical prices
# ══════════════════════════════════════════════════════════════════════════════

def fetch_comp_data() -> dict:
    """Download historical price data for comp companies."""
    print("Fetching comparable-company data from Yahoo Finance...")
    comp_data = {}
    for ticker, info in COMPS.items():
        try:
            df = yf.download(
                ticker,
                start=info["ipo_date"],
                end="2026-05-20",
                auto_adjust=True,
                progress=False,
            )
            if df.empty:
                print(f"  WARNING: No data for {ticker}, generating synthetic fallback.")
                df = _synthetic_comp_fallback(ticker, info)
            else:
                df = df[["Close", "Volume"]].copy()
                df.columns = ["close", "volume"]
                df.index = pd.to_datetime(df.index)
                print(f"  {ticker}: {len(df)} trading days from {df.index[0].date()}")
            comp_data[ticker] = df
        except Exception as exc:
            print(f"  WARNING: {ticker} fetch failed ({exc}); using synthetic fallback.")
            comp_data[ticker] = _synthetic_comp_fallback(ticker, info)
    return comp_data


def _synthetic_comp_fallback(ticker: str, info: dict) -> pd.DataFrame:
    """Generate synthetic comp data when Yahoo Finance is unavailable."""
    rng = np.random.default_rng(abs(hash(ticker)) % (2**31))
    start = pd.to_datetime(info["ipo_date"])
    end   = pd.to_datetime("2026-05-20")
    dates = pd.bdate_range(start, end)
    n     = len(dates)
    # Characteristic params per ticker
    drift_map = {"SNOW": 0.0008, "MDB": 0.0012, "CFLT": 0.0003,
                 "HCP":  0.0005, "ESTC": 0.0007}
    vol_map   = {"SNOW": 0.045,  "MDB": 0.040,  "CFLT": 0.050,
                 "HCP":  0.038,  "ESTC": 0.042}
    mu  = drift_map.get(ticker, 0.0006)
    sig = vol_map.get(ticker, 0.042)
    returns = rng.normal(mu, sig, n)
    prices  = info["ipo_price"] * np.exp(np.cumsum(returns))
    volumes = rng.integers(500_000, 5_000_000, n).astype(float)
    return pd.DataFrame({"close": prices, "volume": volumes}, index=dates)


# ══════════════════════════════════════════════════════════════════════════════
# 2.  SYNTHETIC DATABRICKS PRICE HISTORY (GBM seeded from comps)
# ══════════════════════════════════════════════════════════════════════════════

def compute_comp_post_ipo_stats(comp_data: dict) -> dict:
    """
    Compute annualised drift and daily volatility from each comp's
    first 126 trading days (≈ 6 months) post-IPO.
    """
    drifts = []
    vols   = []
    first_day_returns = []
    first_month_returns = []

    for ticker, df in comp_data.items():
        if len(df) < 20:
            continue
        window = df["close"].iloc[:126]
        log_r  = np.log(window / window.shift(1)).dropna()
        drifts.append(log_r.mean())
        vols.append(log_r.std())

        # First-day return (open->close day 1)
        first_day_returns.append((df["close"].iloc[1] / df["close"].iloc[0]) - 1)
        # First-month return (day 0 -> day 21)
        idx = min(21, len(df) - 1)
        first_month_returns.append((df["close"].iloc[idx] / df["close"].iloc[0]) - 1)

    return {
        "mean_drift": float(np.mean(drifts)),
        "mean_vol":   float(np.mean(vols)),
        "first_day_return_mean":   float(np.mean(first_day_returns)),
        "first_month_return_mean": float(np.mean(first_month_returns)),
        "per_ticker_vol": {t: np.log(comp_data[t]["close"] / comp_data[t]["close"].shift(1)).dropna().std()
                           for t in comp_data},
    }


def simulate_databricks_history(stats: dict) -> pd.DataFrame:
    """
    Simulate Databricks daily price history from IPO_DATE to ANALYSIS_DATE
    using Geometric Brownian Motion calibrated to comp stats.
    """
    trading_days = pd.bdate_range(IPO_DATE, ANALYSIS_DATE)
    n = len(trading_days)

    mu  = stats["mean_drift"]
    sig = stats["mean_vol"]

    # GBM simulation
    rng = np.random.default_rng(42)
    daily_returns = rng.normal(mu, sig, n)

    # Inject a realistic first-day pop then slight first-month drift
    first_day_pop = stats["first_day_return_mean"] * 1.10   # DBRX slightly hotter
    daily_returns[0] = first_day_pop

    prices = IPO_PRICE * np.exp(np.cumsum(daily_returns))

    # Add mild momentum regime: slight sell-off wk2-4, recovery from wk5
    regime_factor = np.ones(n)
    regime_factor[5:22]  = 0.9985   # lock-up jitters
    regime_factor[22:60] = 1.0008   # institutional accumulation
    prices = prices * np.cumprod(regime_factor)

    # Volume: high on day 1, normalises after
    base_vol = 8_000_000
    volume = np.full(n, base_vol, dtype=float)
    volume[0]   *= 5.0
    volume[1:5] *= 2.5
    volume[5:]  = (rng.integers(2_000_000, 12_000_000, n - 5)).astype(float)

    df = pd.DataFrame({
        "date":   trading_days,
        "open":   prices * (1 - np.abs(rng.normal(0, 0.005, n))),
        "high":   prices * (1 + np.abs(rng.normal(0, 0.012, n))),
        "low":    prices * (1 - np.abs(rng.normal(0, 0.012, n))),
        "close":  prices,
        "volume": volume,
    }).set_index("date")

    return df


# ══════════════════════════════════════════════════════════════════════════════
# 3.  FORECASTING MODELS
# ══════════════════════════════════════════════════════════════════════════════

def run_prophet(dbrx_df: pd.DataFrame, forecast_days: int) -> pd.DataFrame:
    """Fit Facebook Prophet and return forecast dataframe."""
    prophet_df = dbrx_df["close"].reset_index()
    prophet_df.columns = ["ds", "y"]
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])

    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=False,
        changepoint_prior_scale=0.15,
        seasonality_mode="multiplicative",
        interval_width=0.80,
    )
    model.fit(prophet_df)

    future    = model.make_future_dataframe(periods=forecast_days, freq="B")
    forecast  = model.predict(future)
    return forecast


def run_arima(dbrx_df: pd.DataFrame, forecast_days: int) -> pd.DataFrame:
    """Fit ARIMA(2,1,2) and return forecast with confidence intervals."""
    prices = dbrx_df["close"].values
    model  = ARIMA(prices, order=(2, 1, 2))
    result = model.fit()

    fc_obj = result.get_forecast(steps=forecast_days)
    fc_mean = fc_obj.predicted_mean
    fc_ci   = fc_obj.conf_int(alpha=0.20)   # 80% CI

    last_date = dbrx_df.index[-1]
    fc_dates  = pd.bdate_range(last_date + timedelta(days=1), periods=forecast_days)

    return pd.DataFrame({
        "date":       fc_dates,
        "yhat":       fc_mean,
        "yhat_lower": fc_ci[:, 0],
        "yhat_upper": fc_ci[:, 1],
    }).set_index("date")


def run_linear_regression(dbrx_df: pd.DataFrame, forecast_days: int) -> pd.DataFrame:
    """Fit log-price linear regression and return forecast."""
    df = dbrx_df["close"].copy()
    X  = np.arange(len(df)).reshape(-1, 1)
    y  = np.log(df.values)

    reg = LinearRegression()
    reg.fit(X, y)

    future_idx   = np.arange(len(df), len(df) + forecast_days).reshape(-1, 1)
    log_forecast = reg.predict(future_idx)
    forecast     = np.exp(log_forecast)

    last_date = dbrx_df.index[-1]
    fc_dates  = pd.bdate_range(last_date + timedelta(days=1), periods=forecast_days)

    # Simple prediction interval (±1.5 std of residuals)
    residuals = y - reg.predict(X)
    std_resid  = residuals.std()
    # Propagate uncertainty: grows with sqrt(t)
    horizon   = np.arange(1, forecast_days + 1)
    spread    = std_resid * np.sqrt(horizon)

    return pd.DataFrame({
        "date":       fc_dates,
        "yhat":       forecast,
        "yhat_lower": np.exp(log_forecast - 1.96 * spread),
        "yhat_upper": np.exp(log_forecast + 1.96 * spread),
    }).set_index("date")


# ══════════════════════════════════════════════════════════════════════════════
# 4.  CHARTS
# ══════════════════════════════════════════════════════════════════════════════

def chart_01_price_history(dbrx_df: pd.DataFrame) -> None:
    """Chart 1: Databricks price history with volume."""
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 8), gridspec_kw={"height_ratios": [3, 1]}, sharex=True
    )
    fig.suptitle(
        "Databricks (DBRX) — Price History Since IPO\n"
        f"IPO Price: ${IPO_PRICE:.2f}  |  IPO Date: {IPO_DATE.strftime('%b %d, %Y')}",
        fontsize=15, fontweight="bold", y=1.01,
    )

    # Price line + fill
    ax1.plot(dbrx_df.index, dbrx_df["close"], color=PALETTE["primary"], lw=1.8, label="Close Price")
    ax1.fill_between(dbrx_df.index, dbrx_df["close"], IPO_PRICE,
                     where=(dbrx_df["close"] >= IPO_PRICE),
                     alpha=0.15, color="green", label="Above IPO")
    ax1.fill_between(dbrx_df.index, dbrx_df["close"], IPO_PRICE,
                     where=(dbrx_df["close"] < IPO_PRICE),
                     alpha=0.15, color="red", label="Below IPO")
    ax1.axhline(IPO_PRICE, color="gray", ls="--", lw=1.2, label=f"IPO Price ${IPO_PRICE:.2f}")

    # 20-day MA
    ma20 = dbrx_df["close"].rolling(20).mean()
    ax1.plot(dbrx_df.index, ma20, color=PALETTE["secondary"], lw=1.2, ls="--", label="20-day MA")

    current = dbrx_df["close"].iloc[-1]
    pct_chg = (current / IPO_PRICE - 1) * 100
    ax1.set_ylabel("Price (USD)", fontsize=12)
    ax1.legend(loc="upper left", fontsize=9)
    ax1.set_title(
        f"Current: ${current:.2f}  ({pct_chg:+.1f}% vs IPO)",
        fontsize=11, loc="right", color=PALETTE["accent"],
    )

    # Volume bars
    colors = ["green" if c >= o else "red"
              for c, o in zip(dbrx_df["close"], dbrx_df["open"])]
    ax2.bar(dbrx_df.index, dbrx_df["volume"] / 1e6, color=colors, alpha=0.7, width=1)
    ax2.set_ylabel("Volume (M)", fontsize=10)
    ax2.set_xlabel("Date", fontsize=11)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator())
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=30, ha="right")

    fig.tight_layout()
    out = os.path.join(CHARTS_DIR, "01_ipo_price_history.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def chart_02_comp_analysis(comp_data: dict, dbrx_df: pd.DataFrame) -> None:
    """Chart 2: Normalised price performance vs comps since their IPOs."""
    fig, ax = plt.subplots(figsize=(14, 7))
    fig.suptitle(
        "Normalised Post-IPO Price Performance: DBRX vs Tech IPO Comps",
        fontsize=14, fontweight="bold",
    )

    comp_colors = plt.cm.tab10(np.linspace(0, 1, len(COMPS)))

    for (ticker, info), color in zip(COMPS.items(), comp_colors):
        df = comp_data[ticker]
        if len(df) < 2:
            continue
        # Trim to first 100 trading days for a fair IPO comparison window
        window = min(100, len(df))
        norm   = (df["close"].iloc[:window] / df["close"].iloc[0]) * 100
        ax.plot(range(window), norm.values, color=color, lw=1.4,
                alpha=0.75, label=f"{ticker} ({info['name']})")

    # Databricks (full history — may be < 100 days)
    dbrx_norm = (dbrx_df["close"] / dbrx_df["close"].iloc[0]) * 100
    ax.plot(range(len(dbrx_norm)), dbrx_norm.values,
            color=PALETTE["primary"], lw=2.5, label="DBRX (Databricks)", zorder=5)

    ax.axhline(100, color="gray", ls="--", lw=1)
    ax.set_xlabel("Trading Days Since IPO", fontsize=12)
    ax.set_ylabel("Indexed Price (IPO Day = 100)", fontsize=12)
    ax.legend(loc="upper left", fontsize=9, ncol=2)
    ax.set_xlim(0)

    fig.tight_layout()
    out = os.path.join(CHARTS_DIR, "02_comp_analysis.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def chart_03_prophet_forecast(dbrx_df: pd.DataFrame, prophet_fc: pd.DataFrame) -> None:
    """Chart 3: Prophet forecast with 80% and 95% confidence bands."""
    fig, ax = plt.subplots(figsize=(14, 7))

    hist_end = dbrx_df.index[-1]

    # Historical
    ax.plot(dbrx_df.index, dbrx_df["close"],
            color=PALETTE["accent"], lw=1.8, label="Historical Price", zorder=4)

    # Forecast portion only
    fc_future = prophet_fc[prophet_fc["ds"] > hist_end].copy()
    fc_full   = prophet_fc.copy()

    # 80% CI (from Prophet)
    ax.fill_between(fc_future["ds"], fc_future["yhat_lower"], fc_future["yhat_upper"],
                    color=PALETTE["prophet"], alpha=0.25, label="80% Confidence Interval")

    # 95% CI: approximate as ±1.96/1.28 * (yhat_upper - yhat_lower)
    ci_half   = (fc_future["yhat_upper"] - fc_future["yhat_lower"]) / 2 / 1.28 * 1.96
    ax.fill_between(fc_future["ds"],
                    fc_future["yhat"] - ci_half,
                    fc_future["yhat"] + ci_half,
                    color=PALETTE["prophet"], alpha=0.10, label="95% Confidence Interval")

    ax.plot(fc_future["ds"], fc_future["yhat"],
            color=PALETTE["prophet"], lw=2, ls="--", label="Prophet Forecast", zorder=5)

    # In-sample fitted
    fc_hist = fc_full[fc_full["ds"] <= hist_end]
    ax.plot(fc_hist["ds"], fc_hist["yhat"],
            color=PALETTE["prophet"], lw=1, alpha=0.5, ls=":", label="Prophet In-sample Fit")

    ax.axvline(hist_end, color="gray", ls="--", lw=1, label="Forecast Start")
    ax.axhline(IPO_PRICE, color="gray", ls=":", lw=0.8)

    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Price (USD)", fontsize=12)
    ax.set_title("Facebook Prophet — 90 & 180-Day Forecast with Confidence Bands",
                 fontsize=12, loc="left")
    ax.legend(loc="upper left", fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")

    fig.tight_layout()
    out = os.path.join(CHARTS_DIR, "03_prophet_forecast.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


def chart_04_model_comparison(
    dbrx_df: pd.DataFrame,
    prophet_fc: pd.DataFrame,
    arima_fc: pd.DataFrame,
    linreg_fc: pd.DataFrame,
) -> None:
    """Chart 4: All 3 models' 90-day forecasts overlaid."""
    fig, ax = plt.subplots(figsize=(14, 7))

    hist_end  = dbrx_df.index[-1]
    last_n    = 60   # show last 60 days of history for context

    ax.plot(dbrx_df.index[-last_n:], dbrx_df["close"].iloc[-last_n:],
            color=PALETTE["accent"], lw=2, label="Historical (last 60 days)", zorder=5)

    # Prophet
    fc_p = prophet_fc[prophet_fc["ds"] > hist_end].iloc[:FORECAST_DAYS_SHORT]
    ax.plot(fc_p["ds"], fc_p["yhat"],
            color=PALETTE["prophet"], lw=2, ls="--", label="Prophet", zorder=4)
    ax.fill_between(fc_p["ds"], fc_p["yhat_lower"], fc_p["yhat_upper"],
                    color=PALETTE["prophet"], alpha=0.12)

    # ARIMA
    ax.plot(arima_fc.index, arima_fc["yhat"],
            color=PALETTE["arima"], lw=2, ls="-.", label="ARIMA(2,1,2)", zorder=4)
    ax.fill_between(arima_fc.index, arima_fc["yhat_lower"], arima_fc["yhat_upper"],
                    color=PALETTE["arima"], alpha=0.10)

    # Linear Regression
    ax.plot(linreg_fc.index, linreg_fc["yhat"],
            color=PALETTE["linreg"], lw=2, ls=":", label="Log-Linear Regression", zorder=4)
    ax.fill_between(linreg_fc.index, linreg_fc["yhat_lower"], linreg_fc["yhat_upper"],
                    color=PALETTE["linreg"], alpha=0.08)

    ax.axvline(hist_end, color="gray", ls="--", lw=1, label="Forecast Start")

    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Price (USD)", fontsize=12)
    ax.set_title("90-Day Price Forecast — Model Comparison (Prophet / ARIMA / Log-Linear)",
                 fontsize=12, loc="left")
    ax.legend(loc="upper left", fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")

    fig.tight_layout()
    out = os.path.join(CHARTS_DIR, "04_model_comparison.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


# ══════════════════════════════════════════════════════════════════════════════
# 5.  SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════════════

def print_summary(dbrx_df: pd.DataFrame, prophet_fc: pd.DataFrame, stats: dict) -> None:
    """Print a formatted summary table."""
    current = dbrx_df["close"].iloc[-1]
    hist_end = dbrx_df.index[-1]

    fc_future = prophet_fc[prophet_fc["ds"] > hist_end].reset_index(drop=True)

    horizons = {30: None, 60: None, 90: None}
    for h in horizons:
        idx = min(h - 1, len(fc_future) - 1)
        if idx >= 0:
            horizons[h] = fc_future.iloc[idx]

    # Bull/Base/Bear at day 90
    row90 = horizons[90]
    if row90 is not None:
        base  = row90["yhat"]
        bull  = row90["yhat_upper"]
        bear  = row90["yhat_lower"]
    else:
        base = bear = bull = current

    separator = "─" * 66
    print(f"\n{'═' * 66}")
    print(f"  DATABRICKS (DBRX) — FORECAST SUMMARY  |  As of {ANALYSIS_DATE.strftime('%Y-%m-%d')}")
    print(f"{'═' * 66}")
    print(f"  IPO Date     : {IPO_DATE.strftime('%Y-%m-%d')}   IPO Price : ${IPO_PRICE:.2f}")
    print(f"  Current Price: ${current:.2f}   Since IPO : {(current/IPO_PRICE - 1)*100:+.1f}%")
    print(f"  Comp Avg Vol : {stats['mean_vol']*100:.2f}%/day   Avg Drift : {stats['mean_drift']*100:.4f}%/day")
    print(f"{separator}")
    print(f"  {'Horizon':<10} {'Prophet ($)':<14} {'vs Current':>11}")
    print(f"{separator}")
    for h, row in horizons.items():
        if row is not None:
            p   = row["yhat"]
            pct = (p / current - 1) * 100
            print(f"  {h}-day     {p:>10.2f}      {pct:>+10.1f}%")
    print(f"{separator}")
    print(f"  90-Day Scenarios (Prophet):")
    print(f"    Bull  (+1σ)  : ${bull:.2f}   ({(bull/current-1)*100:+.1f}% vs current)")
    print(f"    Base  (mean) : ${base:.2f}   ({(base/current-1)*100:+.1f}% vs current)")
    print(f"    Bear  (-1σ)  : ${bear:.2f}   ({(bear/current-1)*100:+.1f}% vs current)")
    print(f"{'═' * 66}\n")
    print("  Key Risk Factors:")
    print("    - Lock-up expiry ~90-120 days post-IPO may cause selling pressure")
    print("    - Macro rate sensitivity: high-growth tech multiples compress with rate hikes")
    print("    - Competitor moves: Snowflake, Palantir, Cloudera (private) in data AI space")
    print("    - Revenue growth rate deceleration risk (common in Y1-2 post-IPO)")
    print("    - Model risk: synthetic history calibrated to comps; not real trading data")
    print(f"{'═' * 66}\n")


# ══════════════════════════════════════════════════════════════════════════════
# 6.  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 66)
    print("  DATABRICKS POST-IPO STOCK FORECAST")
    print("=" * 66)

    # Step 1: Fetch comp data
    comp_data = fetch_comp_data()

    # Step 2: Compute stats from comps
    print("\nComputing comp post-IPO statistics...")
    stats = compute_comp_post_ipo_stats(comp_data)
    print(f"  Mean daily drift : {stats['mean_drift']*100:.4f}%")
    print(f"  Mean daily vol   : {stats['mean_vol']*100:.2f}%")
    print(f"  Avg 1st-day pop  : {stats['first_day_return_mean']*100:.1f}%")
    print(f"  Avg 1st-month rtn: {stats['first_month_return_mean']*100:.1f}%")

    # Step 3: Simulate Databricks history
    print("\nSimulating Databricks price history (GBM)...")
    dbrx_df = simulate_databricks_history(stats)
    print(f"  Generated {len(dbrx_df)} trading days: "
          f"{dbrx_df.index[0].date()} → {dbrx_df.index[-1].date()}")
    print(f"  IPO price: ${IPO_PRICE:.2f}  |  Current: ${dbrx_df['close'].iloc[-1]:.2f}")

    # Step 4: Run models
    print("\nRunning forecasting models...")
    print("  [1/3] Facebook Prophet (180-day)...")
    prophet_fc = run_prophet(dbrx_df, FORECAST_DAYS_LONG)

    print("  [2/3] ARIMA(2,1,2) (90-day)...")
    arima_fc = run_arima(dbrx_df, FORECAST_DAYS_SHORT)

    print("  [3/3] Log-Linear Regression (90-day)...")
    linreg_fc = run_linear_regression(dbrx_df, FORECAST_DAYS_SHORT)

    # Step 5: Charts
    print("\nGenerating charts...")
    chart_01_price_history(dbrx_df)
    chart_02_comp_analysis(comp_data, dbrx_df)
    chart_03_prophet_forecast(dbrx_df, prophet_fc)
    chart_04_model_comparison(dbrx_df, prophet_fc, arima_fc, linreg_fc)

    # Step 6: Summary
    print_summary(dbrx_df, prophet_fc, stats)

    print(f"All outputs written to: {CHARTS_DIR}/")
    print("Done.\n")


if __name__ == "__main__":
    main()
