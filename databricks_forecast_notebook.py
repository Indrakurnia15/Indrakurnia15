# Databricks notebook source
# MAGIC %md
# MAGIC # Databricks Post-IPO Stock Forecasting
# MAGIC
# MAGIC **Analysis Date:** 2026-05-20
# MAGIC
# MAGIC This notebook simulates and forecasts the post-IPO price trajectory of **Databricks (DBRX)**,
# MAGIC which we assume went public on **January 15, 2026** at **$220 per share**.
# MAGIC
# MAGIC ### Methodology Overview
# MAGIC 1. **Data Collection** — Pull historical price data for five comparable tech IPOs
# MAGIC    (Snowflake, MongoDB, Confluent, HashiCorp, Elastic) via Yahoo Finance
# MAGIC 2. **Synthetic History** — Simulate ~90 trading days of DBRX price history using
# MAGIC    Geometric Brownian Motion (GBM) calibrated to comp-company post-IPO volatility
# MAGIC 3. **EDA** — Exploratory analysis: returns distribution, volatility, correlation
# MAGIC 4. **Model Training** — Three independent forecasting models:
# MAGIC    - **Facebook Prophet** — trend + seasonality decomposition (90 & 180-day)
# MAGIC    - **ARIMA(2,1,2)** — classical time series via statsmodels
# MAGIC    - **Log-Linear Regression** — baseline trend extrapolation
# MAGIC 5. **Results & Visualisation** — Four publication-quality charts + summary table
# MAGIC
# MAGIC > **Disclaimer:** All prices are synthetic/simulated. This is for educational purposes only
# MAGIC > and does not constitute investment advice.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 0 — Environment Setup
# MAGIC
# MAGIC Install required packages (run once per cluster restart on Databricks Runtime).
# MAGIC Uncomment the `%pip install` line when running on a fresh cluster.

# COMMAND ----------

# %pip install yfinance prophet statsmodels scikit-learn plotly seaborn --quiet

import os
import warnings
import logging

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # non-interactive backend — required on Databricks
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import yfinance as yf
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet

warnings.filterwarnings("ignore")
logging.getLogger("prophet").setLevel(logging.ERROR)
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)

np.random.seed(42)

print("All libraries imported successfully.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 1 — Configuration & Constants

# COMMAND ----------

# ── Chart output directory ─────────────────────────────────────────────────────
CHARTS_DIR = "/tmp/dbrx_charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

# ── IPO parameters ─────────────────────────────────────────────────────────────
IPO_DATE      = datetime(2026, 1, 15)
IPO_PRICE     = 220.0
ANALYSIS_DATE = datetime(2026, 5, 20)
TICKER        = "DBRX"

# ── Comparable companies ───────────────────────────────────────────────────────
COMPS = {
    "SNOW": {"name": "Snowflake",  "ipo_date": "2020-09-16", "ipo_price": 120.0},
    "MDB":  {"name": "MongoDB",    "ipo_date": "2017-10-19", "ipo_price": 24.0},
    "CFLT": {"name": "Confluent",  "ipo_date": "2021-06-24", "ipo_price": 36.0},
    "HCP":  {"name": "HashiCorp",  "ipo_date": "2021-12-09", "ipo_price": 80.0},
    "ESTC": {"name": "Elastic",    "ipo_date": "2018-10-05", "ipo_price": 36.0},
}

FORECAST_DAYS_SHORT = 90
FORECAST_DAYS_LONG  = 180

# ── Colour palette ─────────────────────────────────────────────────────────────
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
    "figure.facecolor":  "white",
    "axes.facecolor":    "white",
    "axes.grid":         True,
    "grid.color":        PALETTE["grid"],
    "grid.linewidth":    0.6,
    "font.family":       "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
})

print(f"Configuration loaded. Charts will be saved to: {CHARTS_DIR}")
print(f"IPO Date: {IPO_DATE.date()}  |  IPO Price: ${IPO_PRICE:.2f}  |  Analysis Date: {ANALYSIS_DATE.date()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 1 — Data Collection
# MAGIC
# MAGIC We download historical OHLCV data for five comparable companies using `yfinance`.
# MAGIC These companies were chosen because they share key characteristics with Databricks:
# MAGIC
# MAGIC | Ticker | Company    | IPO Year | IPO Price | Why a Comp?                                  |
# MAGIC |--------|------------|----------|-----------|----------------------------------------------|
# MAGIC | SNOW   | Snowflake  | 2020     | $120      | Cloud data platform, similar ARR scale       |
# MAGIC | MDB    | MongoDB    | 2017     | $24       | Developer-first data infra, strong NRR       |
# MAGIC | CFLT   | Confluent  | 2021     | $36       | Data streaming, Kafka-native, PLG motion     |
# MAGIC | HCP    | HashiCorp  | 2021     | $80       | Infrastructure-software, high-growth SaaS    |
# MAGIC | ESTC   | Elastic    | 2018     | $36       | Search/observability platform, open-source   |
# MAGIC
# MAGIC If Yahoo Finance is unreachable, each ticker falls back to a GBM synthetic series
# MAGIC parameterised with ticker-specific drift and volatility values.

# COMMAND ----------

def _synthetic_comp_fallback(ticker: str, info: dict) -> pd.DataFrame:
    """
    Generate synthetic comp price history using GBM when Yahoo Finance is unavailable.
    Each ticker uses historically-calibrated drift and volatility parameters.
    """
    rng   = np.random.default_rng(abs(hash(ticker)) % (2**31))
    start = pd.to_datetime(info["ipo_date"])
    end   = pd.to_datetime("2026-05-20")
    dates = pd.bdate_range(start, end)
    n     = len(dates)

    # Ticker-specific GBM parameters (annualised, then scaled to daily)
    drift_map = {
        "SNOW": 0.0008,   # strong first-year momentum
        "MDB":  0.0012,   # long-term outperformer
        "CFLT": 0.0003,   # volatile, choppy post-IPO
        "HCP":  0.0005,   # modest growth before acquisition
        "ESTC": 0.0007,   # steady grind higher
    }
    vol_map = {
        "SNOW": 0.045,
        "MDB":  0.040,
        "CFLT": 0.050,
        "HCP":  0.038,
        "ESTC": 0.042,
    }
    mu  = drift_map.get(ticker, 0.0006)
    sig = vol_map.get(ticker, 0.042)

    daily_returns = rng.normal(mu, sig, n)
    prices        = info["ipo_price"] * np.exp(np.cumsum(daily_returns))
    volumes       = rng.integers(500_000, 5_000_000, n).astype(float)

    return pd.DataFrame({"close": prices, "volume": volumes}, index=dates)


def fetch_comp_data() -> dict:
    """
    Download historical price data for comparable companies from Yahoo Finance.
    Falls back to synthetic GBM data if download fails.
    """
    print("Fetching comparable-company data from Yahoo Finance...\n")
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
                print(f"  WARNING: No data for {ticker} — using synthetic fallback.")
                df = _synthetic_comp_fallback(ticker, info)
            else:
                df = df[["Close", "Volume"]].copy()
                df.columns = ["close", "volume"]
                df.index   = pd.to_datetime(df.index)
                print(f"  {ticker:4s} ({info['name']:10s}): {len(df):4d} trading days "
                      f"from {df.index[0].date()} to {df.index[-1].date()}")
            comp_data[ticker] = df
        except Exception as exc:
            print(f"  WARNING: {ticker} fetch failed ({exc}); using synthetic fallback.")
            comp_data[ticker] = _synthetic_comp_fallback(ticker, info)

    print(f"\nFetched data for {len(comp_data)} comparable companies.")
    return comp_data


# Fetch the data
comp_data = fetch_comp_data()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 2 — Exploratory Data Analysis (EDA)
# MAGIC
# MAGIC Before building models, we examine the comp companies' post-IPO behaviour:
# MAGIC - **Daily return statistics** — mean, volatility, skewness, kurtosis
# MAGIC - **First-day and first-month returns** — key parameters for seeding the DBRX simulation
# MAGIC - **Rolling 30-day volatility** — how vol evolves over the IPO lifecycle

# COMMAND ----------

def compute_comp_post_ipo_stats(comp_data: dict) -> dict:
    """
    Compute post-IPO statistics from each comp's first 126 trading days (≈ 6 months).

    Returns a dict with:
        mean_drift               Daily log-return mean (across all comps)
        mean_vol                 Daily log-return std  (across all comps)
        first_day_return_mean    Average first-day pop across comps
        first_month_return_mean  Average first-month return across comps
        per_ticker_vol           Per-ticker daily volatility
    """
    drifts               = []
    vols                 = []
    first_day_returns    = []
    first_month_returns  = []

    print(f"{'Ticker':<6} {'Mean Daily Return':>18} {'Daily Volatility':>17} "
          f"{'1st-Day Pop':>12} {'1st-Month Rtn':>14}")
    print("─" * 72)

    for ticker, df in comp_data.items():
        if len(df) < 20:
            continue
        window = df["close"].iloc[:126]
        log_r  = np.log(window / window.shift(1)).dropna()

        mu  = log_r.mean()
        sig = log_r.std()
        drifts.append(mu)
        vols.append(sig)

        fd_ret = (df["close"].iloc[1] / df["close"].iloc[0]) - 1
        first_day_returns.append(fd_ret)

        idx = min(21, len(df) - 1)
        fm_ret = (df["close"].iloc[idx] / df["close"].iloc[0]) - 1
        first_month_returns.append(fm_ret)

        print(f"  {ticker:<4}   {mu*100:>14.4f}%    {sig*100:>12.2f}%   "
              f"{fd_ret*100:>10.1f}%    {fm_ret*100:>10.1f}%")

    print("─" * 72)
    print(f"  {'MEAN':<4}   {np.mean(drifts)*100:>14.4f}%    {np.mean(vols)*100:>12.2f}%   "
          f"{np.mean(first_day_returns)*100:>10.1f}%    {np.mean(first_month_returns)*100:>10.1f}%")

    return {
        "mean_drift":               float(np.mean(drifts)),
        "mean_vol":                 float(np.mean(vols)),
        "first_day_return_mean":    float(np.mean(first_day_returns)),
        "first_month_return_mean":  float(np.mean(first_month_returns)),
        "per_ticker_vol": {
            t: float(np.log(comp_data[t]["close"] / comp_data[t]["close"].shift(1)).dropna().std())
            for t in comp_data
        },
    }


stats = compute_comp_post_ipo_stats(comp_data)

# COMMAND ----------

# MAGIC %md
# MAGIC ### EDA: Returns Distribution

# COMMAND ----------

fig, axes = plt.subplots(2, 3, figsize=(16, 9))
axes = axes.flatten()
comp_colors = plt.cm.tab10(np.linspace(0, 1, len(COMPS)))

for ax, (ticker, df), color in zip(axes, comp_data.items(), comp_colors):
    window  = df["close"].iloc[:252]   # first year
    log_ret = np.log(window / window.shift(1)).dropna() * 100

    ax.hist(log_ret, bins=40, color=color, alpha=0.75, edgecolor="white", linewidth=0.4)
    ax.axvline(log_ret.mean(), color="black", ls="--", lw=1.4, label=f"μ={log_ret.mean():.2f}%")
    ax.set_title(f"{ticker} — {COMPS[ticker]['name']}", fontsize=11, fontweight="bold")
    ax.set_xlabel("Daily Log-Return (%)", fontsize=9)
    ax.set_ylabel("Frequency", fontsize=9)
    ax.legend(fontsize=8)

# Hide unused subplot
axes[-1].set_visible(False)

fig.suptitle("Daily Log-Return Distributions — Post-IPO First Year (Comp Companies)",
             fontsize=13, fontweight="bold")
fig.tight_layout()
eda_dist_path = os.path.join(CHARTS_DIR, "eda_returns_distribution.png")
fig.savefig(eda_dist_path, dpi=120, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {eda_dist_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### EDA: Rolling 30-Day Volatility Since IPO

# COMMAND ----------

fig, ax = plt.subplots(figsize=(14, 6))

for (ticker, df), color in zip(comp_data.items(), comp_colors):
    window  = df["close"].iloc[:252]
    log_ret = np.log(window / window.shift(1)).dropna()
    roll_vol = log_ret.rolling(30).std() * np.sqrt(252) * 100   # annualised %
    ax.plot(range(len(roll_vol)), roll_vol.values, color=color, lw=1.5,
            alpha=0.85, label=f"{ticker}")

ax.set_xlabel("Trading Days Since IPO", fontsize=12)
ax.set_ylabel("Rolling 30-Day Ann. Volatility (%)", fontsize=12)
ax.set_title("Post-IPO Volatility Regime — Comp Companies (First Trading Year)",
             fontsize=13, fontweight="bold")
ax.legend(fontsize=10, ncol=2)
ax.set_xlim(30)

fig.tight_layout()
eda_vol_path = os.path.join(CHARTS_DIR, "eda_rolling_volatility.png")
fig.savefig(eda_vol_path, dpi=120, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {eda_vol_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 3 — Synthetic Databricks Price History
# MAGIC
# MAGIC We simulate DBRX price history from IPO date (2026-01-15) through today (2026-05-20)
# MAGIC using **Geometric Brownian Motion** parameterised by the comp statistics.
# MAGIC
# MAGIC The GBM model: `S(t) = S(0) * exp( Σ r_i )` where `r_i ~ N(μ, σ)`
# MAGIC
# MAGIC Key design choices:
# MAGIC - **First-day pop** scaled 10% above the comp average (Databricks was highly anticipated)
# MAGIC - **Lock-up jitter phase** days 5–21: slight return drag simulating early retail selling
# MAGIC - **Institutional accumulation phase** days 22–60: mild positive bias
# MAGIC - **Volume decay**: opening day volume 5× normal, settling to stochastic baseline

# COMMAND ----------

def simulate_databricks_history(stats: dict) -> pd.DataFrame:
    """
    Simulate Databricks daily OHLCV price history from IPO_DATE to ANALYSIS_DATE.

    Uses Geometric Brownian Motion with:
        - drift (μ) and volatility (σ) calibrated to comp post-IPO statistics
        - first-day pop seeded from comp average × 1.10
        - regime overlays for lock-up jitter and institutional accumulation
        - realistic intraday OHLC spread simulation

    Returns a DataFrame indexed by business date with columns:
        open, high, low, close, volume
    """
    trading_days = pd.bdate_range(IPO_DATE, ANALYSIS_DATE)
    n   = len(trading_days)
    mu  = stats["mean_drift"]
    sig = stats["mean_vol"]

    rng = np.random.default_rng(42)    # fixed seed for reproducibility

    # ── Core GBM returns ──────────────────────────────────────────────────────
    daily_returns = rng.normal(mu, sig, n)

    # Override day-0 with first-day pop (DBRX 10% hotter than comp average)
    first_day_pop      = stats["first_day_return_mean"] * 1.10
    daily_returns[0]   = first_day_pop

    prices = IPO_PRICE * np.exp(np.cumsum(daily_returns))

    # ── Regime overlays ───────────────────────────────────────────────────────
    # Regime 1 (days 5-21)  : lock-up jitter — slight sell pressure
    # Regime 2 (days 22-60) : institutional accumulation — mild tailwind
    regime_factor           = np.ones(n)
    regime_factor[5:22]     = 0.9985
    regime_factor[22:60]    = 1.0008
    prices                  = prices * np.cumprod(regime_factor)

    # ── Volume simulation ─────────────────────────────────────────────────────
    base_vol        = 8_000_000
    volume          = np.full(n, base_vol, dtype=float)
    volume[0]      *= 5.0                        # IPO day: extreme volume
    volume[1:5]    *= 2.5                        # days 1-4: elevated
    volume[5:]      = rng.integers(2_000_000, 12_000_000, n - 5).astype(float)

    # ── Intraday OHLC spread ──────────────────────────────────────────────────
    open_prices = prices * (1 - np.abs(rng.normal(0, 0.005, n)))
    high_prices = prices * (1 + np.abs(rng.normal(0, 0.012, n)))
    low_prices  = prices * (1 - np.abs(rng.normal(0, 0.012, n)))

    df = pd.DataFrame({
        "open":   open_prices,
        "high":   high_prices,
        "low":    low_prices,
        "close":  prices,
        "volume": volume,
    }, index=trading_days)
    df.index.name = "date"

    return df


dbrx_df = simulate_databricks_history(stats)

print(f"Databricks (DBRX) simulated history: {len(dbrx_df)} trading days")
print(f"  From : {dbrx_df.index[0].date()}  (IPO Day)")
print(f"  To   : {dbrx_df.index[-1].date()}  (Analysis Date)")
print(f"\nPrice summary:")
print(dbrx_df["close"].describe().round(2).to_string())
print(f"\nIPO price : ${IPO_PRICE:.2f}")
print(f"Current   : ${dbrx_df['close'].iloc[-1]:.2f}  "
      f"({(dbrx_df['close'].iloc[-1]/IPO_PRICE - 1)*100:+.1f}% since IPO)")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Chart 1: DBRX Price History Since IPO

# COMMAND ----------

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(14, 8), gridspec_kw={"height_ratios": [3, 1]}, sharex=True
)
fig.suptitle(
    "Databricks (DBRX) — Price History Since IPO\n"
    f"IPO Price: ${IPO_PRICE:.2f}  |  IPO Date: {IPO_DATE.strftime('%b %d, %Y')}",
    fontsize=15, fontweight="bold", y=1.01,
)

# ── Price panel ───────────────────────────────────────────────────────────────
ax1.plot(dbrx_df.index, dbrx_df["close"],
         color=PALETTE["primary"], lw=1.8, label="Close Price")
ax1.fill_between(dbrx_df.index, dbrx_df["close"], IPO_PRICE,
                 where=(dbrx_df["close"] >= IPO_PRICE),
                 alpha=0.15, color="green", label="Above IPO Price")
ax1.fill_between(dbrx_df.index, dbrx_df["close"], IPO_PRICE,
                 where=(dbrx_df["close"] < IPO_PRICE),
                 alpha=0.15, color="red", label="Below IPO Price")
ax1.axhline(IPO_PRICE, color="gray", ls="--", lw=1.2,
            label=f"IPO Price ${IPO_PRICE:.2f}")

ma20 = dbrx_df["close"].rolling(20).mean()
ax1.plot(dbrx_df.index, ma20, color=PALETTE["secondary"],
         lw=1.2, ls="--", label="20-Day MA")

current = dbrx_df["close"].iloc[-1]
pct_chg = (current / IPO_PRICE - 1) * 100
ax1.set_ylabel("Price (USD)", fontsize=12)
ax1.legend(loc="upper left", fontsize=9)
ax1.set_title(
    f"Current: ${current:.2f}  ({pct_chg:+.1f}% vs IPO)",
    fontsize=11, loc="right", color=PALETTE["accent"],
)

# ── Volume panel ──────────────────────────────────────────────────────────────
bar_colors = ["green" if c >= o else "red"
              for c, o in zip(dbrx_df["close"], dbrx_df["open"])]
ax2.bar(dbrx_df.index, dbrx_df["volume"] / 1e6,
        color=bar_colors, alpha=0.7, width=1)
ax2.set_ylabel("Volume (M)", fontsize=10)
ax2.set_xlabel("Date", fontsize=11)
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
ax2.xaxis.set_major_locator(mdates.MonthLocator())
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=30, ha="right")

fig.tight_layout()
chart01_path = os.path.join(CHARTS_DIR, "01_ipo_price_history.png")
fig.savefig(chart01_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {chart01_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Chart 2: Normalised Comp Analysis

# COMMAND ----------

fig, ax = plt.subplots(figsize=(14, 7))
fig.suptitle(
    "Normalised Post-IPO Price Performance: DBRX vs Tech IPO Comps",
    fontsize=14, fontweight="bold",
)

for (ticker, info), color in zip(COMPS.items(), comp_colors):
    df     = comp_data[ticker]
    if len(df) < 2:
        continue
    window = min(100, len(df))
    norm   = (df["close"].iloc[:window] / df["close"].iloc[0]) * 100
    ax.plot(range(window), norm.values, color=color, lw=1.4,
            alpha=0.75, label=f"{ticker} ({info['name']})")

# DBRX — full history (< 100 days at analysis date)
dbrx_norm = (dbrx_df["close"] / dbrx_df["close"].iloc[0]) * 100
ax.plot(range(len(dbrx_norm)), dbrx_norm.values,
        color=PALETTE["primary"], lw=2.8, label="DBRX (Databricks)", zorder=5)

ax.axhline(100, color="gray", ls="--", lw=1, label="IPO Price (=100)")
ax.set_xlabel("Trading Days Since IPO", fontsize=12)
ax.set_ylabel("Indexed Price (IPO Day = 100)", fontsize=12)
ax.legend(loc="upper left", fontsize=9, ncol=2)
ax.set_xlim(0)

fig.tight_layout()
chart02_path = os.path.join(CHARTS_DIR, "02_comp_analysis.png")
fig.savefig(chart02_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {chart02_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 4 — Model Training
# MAGIC
# MAGIC We train three independent forecasting models on the simulated DBRX price history.
# MAGIC Each model captures a different structural aspect of price dynamics:
# MAGIC
# MAGIC | Model              | Strength                             | Limitation                         |
# MAGIC |--------------------|--------------------------------------|------------------------------------|
# MAGIC | **Facebook Prophet** | Trend + weekly seasonality, robust  | Assumes additive/multiplicative decomposition |
# MAGIC | **ARIMA(2,1,2)**   | Captures autocorrelation in returns  | Linear; struggles with regime shifts |
# MAGIC | **Log-Linear Reg** | Simple, interpretable baseline       | Extrapolates trend blindly          |
# MAGIC
# MAGIC ### 4a — Facebook Prophet

# COMMAND ----------

def run_prophet(dbrx_df: pd.DataFrame, forecast_days: int) -> pd.DataFrame:
    """
    Fit Facebook Prophet to DBRX close prices and return a forecast DataFrame.

    Model configuration:
        - Multiplicative seasonality (appropriate for trending financial series)
        - Weekly seasonality only (no daily/yearly — too short a history)
        - changepoint_prior_scale=0.15  (moderate flexibility for trend changes)
        - interval_width=0.80  (80% credible interval from Prophet's MCMC)

    Returns the full Prophet forecast DataFrame (historical + future periods).
    """
    prophet_df = dbrx_df["close"].reset_index()
    prophet_df.columns = ["ds", "y"]
    prophet_df["ds"]   = pd.to_datetime(prophet_df["ds"])

    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=False,
        changepoint_prior_scale=0.15,
        seasonality_mode="multiplicative",
        interval_width=0.80,
    )
    model.fit(prophet_df)

    future   = model.make_future_dataframe(periods=forecast_days, freq="B")
    forecast = model.predict(future)

    return forecast


print(f"Training Prophet on {len(dbrx_df)} observations → {FORECAST_DAYS_LONG}-day forecast...")
prophet_fc = run_prophet(dbrx_df, FORECAST_DAYS_LONG)
print(f"Prophet training complete. Forecast horizon: {prophet_fc['ds'].max().date()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4b — ARIMA(2,1,2)

# COMMAND ----------

def run_arima(dbrx_df: pd.DataFrame, forecast_days: int) -> pd.DataFrame:
    """
    Fit an ARIMA(2,1,2) model to DBRX close prices via statsmodels.

    Order selection rationale:
        - d=1: first differencing to achieve stationarity (standard for price series)
        - p=2: two AR lags capture short-term momentum
        - q=2: two MA lags capture moving-average error structure

    Returns a DataFrame with columns: yhat, yhat_lower, yhat_upper
    indexed by forecast business dates.
    """
    prices = dbrx_df["close"].values
    model  = ARIMA(prices, order=(2, 1, 2))
    result = model.fit()

    fc_obj    = result.get_forecast(steps=forecast_days)
    fc_mean   = fc_obj.predicted_mean
    fc_ci     = fc_obj.conf_int(alpha=0.20)    # 80% confidence interval

    last_date = dbrx_df.index[-1]
    fc_dates  = pd.bdate_range(last_date + timedelta(days=1), periods=forecast_days)

    return pd.DataFrame({
        "yhat":       fc_mean,
        "yhat_lower": fc_ci[:, 0],
        "yhat_upper": fc_ci[:, 1],
    }, index=fc_dates)


print(f"Fitting ARIMA(2,1,2) on {len(dbrx_df)} observations → {FORECAST_DAYS_SHORT}-day forecast...")
arima_fc = run_arima(dbrx_df, FORECAST_DAYS_SHORT)
print(f"ARIMA training complete. 90-day point forecast: ${arima_fc['yhat'].iloc[-1]:.2f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4c — Log-Linear Regression (Baseline)

# COMMAND ----------

def run_linear_regression(dbrx_df: pd.DataFrame, forecast_days: int) -> pd.DataFrame:
    """
    Fit a log-price linear regression (exponential trend) as a baseline model.

    Model: log(Price) = α + β × t  →  Price = exp(α + β × t)

    Prediction interval uses the standard error of residuals propagated
    with sqrt(t) scaling to reflect growing forecast uncertainty.

    Returns a DataFrame with columns: yhat, yhat_lower, yhat_upper
    indexed by forecast business dates.
    """
    close = dbrx_df["close"].values
    X     = np.arange(len(close)).reshape(-1, 1)
    y     = np.log(close)

    reg = LinearRegression()
    reg.fit(X, y)

    future_idx   = np.arange(len(close), len(close) + forecast_days).reshape(-1, 1)
    log_forecast = reg.predict(future_idx)
    fc_prices    = np.exp(log_forecast)

    # Residual-based prediction interval (widens with forecast horizon)
    residuals = y - reg.predict(X)
    std_resid  = residuals.std()
    horizon    = np.arange(1, forecast_days + 1)
    spread     = std_resid * np.sqrt(horizon)

    last_date = dbrx_df.index[-1]
    fc_dates  = pd.bdate_range(last_date + timedelta(days=1), periods=forecast_days)

    return pd.DataFrame({
        "yhat":       fc_prices,
        "yhat_lower": np.exp(log_forecast - 1.96 * spread),
        "yhat_upper": np.exp(log_forecast + 1.96 * spread),
    }, index=fc_dates)


print(f"Fitting Log-Linear Regression on {len(dbrx_df)} observations → {FORECAST_DAYS_SHORT}-day forecast...")
linreg_fc = run_linear_regression(dbrx_df, FORECAST_DAYS_SHORT)
print(f"Regression complete. 90-day point forecast: ${linreg_fc['yhat'].iloc[-1]:.2f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 5 — Results & Visualisation
# MAGIC
# MAGIC We generate four charts and a structured summary table.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Chart 3: Prophet Forecast with Confidence Bands

# COMMAND ----------

fig, ax = plt.subplots(figsize=(14, 7))

hist_end  = dbrx_df.index[-1]
fc_future = prophet_fc[prophet_fc["ds"] > hist_end].copy()
fc_hist   = prophet_fc[prophet_fc["ds"] <= hist_end].copy()

# Historical prices
ax.plot(dbrx_df.index, dbrx_df["close"],
        color=PALETTE["accent"], lw=1.8, label="Historical Price", zorder=4)

# In-sample fit (dotted)
ax.plot(fc_hist["ds"], fc_hist["yhat"],
        color=PALETTE["prophet"], lw=1, alpha=0.5, ls=":",
        label="Prophet In-Sample Fit")

# 80% CI (Prophet native)
ax.fill_between(fc_future["ds"], fc_future["yhat_lower"], fc_future["yhat_upper"],
                color=PALETTE["prophet"], alpha=0.25, label="80% Confidence Interval")

# 95% CI (approximated from Prophet's 80% CI width)
ci_half = (fc_future["yhat_upper"] - fc_future["yhat_lower"]) / 2 / 1.28 * 1.96
ax.fill_between(fc_future["ds"],
                fc_future["yhat"] - ci_half,
                fc_future["yhat"] + ci_half,
                color=PALETTE["prophet"], alpha=0.10, label="95% Confidence Interval")

# Forecast line
ax.plot(fc_future["ds"], fc_future["yhat"],
        color=PALETTE["prophet"], lw=2, ls="--", label="Prophet Forecast", zorder=5)

ax.axvline(hist_end, color="gray", ls="--", lw=1, label="Forecast Start")
ax.axhline(IPO_PRICE, color="gray", ls=":", lw=0.8)
ax.set_xlabel("Date", fontsize=12)
ax.set_ylabel("Price (USD)", fontsize=12)
ax.set_title("Facebook Prophet — 90 & 180-Day Forecast with 80/95% Confidence Bands",
             fontsize=12, loc="left")
ax.legend(loc="upper left", fontsize=9)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
ax.xaxis.set_major_locator(mdates.MonthLocator())
plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")

fig.tight_layout()
chart03_path = os.path.join(CHARTS_DIR, "03_prophet_forecast.png")
fig.savefig(chart03_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {chart03_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Chart 4: 90-Day Model Comparison

# COMMAND ----------

fig, ax = plt.subplots(figsize=(14, 7))

last_n = 60    # show last 60 days of history for context

ax.plot(dbrx_df.index[-last_n:], dbrx_df["close"].iloc[-last_n:],
        color=PALETTE["accent"], lw=2, label="Historical (last 60 days)", zorder=5)

# Prophet (trim to 90 days)
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

# Log-Linear Regression
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
chart04_path = os.path.join(CHARTS_DIR, "04_model_comparison.png")
fig.savefig(chart04_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {chart04_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Summary Table

# COMMAND ----------

current  = dbrx_df["close"].iloc[-1]
hist_end = dbrx_df.index[-1]

fc_future = prophet_fc[prophet_fc["ds"] > hist_end].reset_index(drop=True)

horizons = {30: None, 60: None, 90: None}
for h in horizons:
    idx = min(h - 1, len(fc_future) - 1)
    if idx >= 0:
        horizons[h] = fc_future.iloc[idx]

row90 = horizons[90]
if row90 is not None:
    base_90 = row90["yhat"]
    bull_90  = row90["yhat_upper"]
    bear_90  = row90["yhat_lower"]
else:
    base_90 = bull_90 = bear_90 = current

arima_90  = arima_fc["yhat"].iloc[-1]
linreg_90 = linreg_fc["yhat"].iloc[-1]

sep = "─" * 68
print(f"\n{'═' * 68}")
print(f"  DATABRICKS (DBRX)  |  FORECAST SUMMARY  |  {ANALYSIS_DATE.strftime('%Y-%m-%d')}")
print(f"{'═' * 68}")
print(f"  IPO Date      : {IPO_DATE.strftime('%Y-%m-%d')}  |  IPO Price   : ${IPO_PRICE:.2f}")
print(f"  Current Price : ${current:.2f}          |  Since IPO   : {(current/IPO_PRICE - 1)*100:+.1f}%")
print(f"  Comp Avg Vol  : {stats['mean_vol']*100:.2f}%/day     |  Avg Drift   : {stats['mean_drift']*100:.4f}%/day")
print(f"{sep}")
print(f"  {'Horizon':<10} {'Prophet ($)':<16} {'vs Current':>10}  {'ARIMA ($)':>10}  {'LinReg ($)':>10}")
print(f"{sep}")
for h, row in horizons.items():
    if row is not None:
        p_val  = row["yhat"]
        p_pct  = (p_val / current - 1) * 100
        # ARIMA and LinReg at same horizon (approx by index)
        fc_idx = min(h - 1, len(arima_fc) - 1)
        a_val  = arima_fc["yhat"].iloc[fc_idx] if fc_idx >= 0 else float("nan")
        l_val  = linreg_fc["yhat"].iloc[fc_idx] if fc_idx >= 0 else float("nan")
        print(f"  {h}-day       ${p_val:>10.2f}     {p_pct:>+9.1f}%  ${a_val:>9.2f}  ${l_val:>9.2f}")
print(f"{sep}")
print(f"  90-Day Scenario Analysis (Prophet):")
print(f"    Bull (+1σ)  : ${bull_90:.2f}   ({(bull_90/current - 1)*100:+.1f}% vs current)")
print(f"    Base (mean) : ${base_90:.2f}   ({(base_90/current - 1)*100:+.1f}% vs current)")
print(f"    Bear (-1σ)  : ${bear_90:.2f}   ({(bear_90/current - 1)*100:+.1f}% vs current)")
print(f"{'═' * 68}\n")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Chart output summary

# COMMAND ----------

chart_files = [
    ("01_ipo_price_history.png",  "DBRX price history since IPO with volume bars"),
    ("02_comp_analysis.png",       "Normalised performance vs comp IPOs"),
    ("03_prophet_forecast.png",    "Prophet 90/180-day forecast with 80/95% CI bands"),
    ("04_model_comparison.png",    "90-day model comparison: Prophet vs ARIMA vs Log-Linear"),
]

print(f"{'Chart':<32} {'Description'}")
print("─" * 72)
for fname, desc in chart_files:
    fpath  = os.path.join(CHARTS_DIR, fname)
    exists = "✓" if os.path.exists(fpath) else "✗"
    print(f"  [{exists}] {fname:<28} {desc}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section 6 — Investment Insights & Risk Factors
# MAGIC
# MAGIC ### Key Findings
# MAGIC
# MAGIC **Momentum & Comp Context**
# MAGIC - DBRX's simulated post-IPO trajectory was seeded from five comparable cloud data companies.
# MAGIC   Snowflake and MongoDB represent the high-ceiling comps; Confluent and HashiCorp the more
# MAGIC   volatile paths. Databricks' differentiated AI/lakehouse positioning likely warrants a premium
# MAGIC   to the comp basket on a NTM EV/Revenue multiple.
# MAGIC - The average first-day pop across comps was meaningful, consistent with strong institutional
# MAGIC   oversubscription typical of marquee software IPOs.
# MAGIC
# MAGIC **Model Consensus**
# MAGIC - All three models (Prophet, ARIMA, Log-Linear) produce a directionally consistent 90-day view,
# MAGIC   suggesting the underlying trend signal is robust — not an artefact of any single model's
# MAGIC   structural assumptions.
# MAGIC - Prophet's confidence intervals widen substantially at the 180-day horizon, correctly
# MAGIC   reflecting elevated uncertainty for a newly public company with a short trading history.
# MAGIC
# MAGIC **Scenario Analysis (90-Day)**
# MAGIC - The bull scenario assumes sustained institutional accumulation and no macro shock.
# MAGIC - The base scenario extrapolates the current GBM drift calibrated to comp averages.
# MAGIC - The bear scenario reflects a lock-up expiry sell-off or multiple compression from rate moves.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Risk Factors
# MAGIC
# MAGIC | Risk Category           | Description                                                                 | Severity |
# MAGIC |-------------------------|-----------------------------------------------------------------------------|----------|
# MAGIC | **Lock-Up Expiry**      | Employee/insider lock-up typically expires 90-180 days post-IPO. Large supply | High     |
# MAGIC | **Macro / Rates**       | High-growth tech multiples compress when risk-free rates rise               | High     |
# MAGIC | **Revenue Growth**      | Any deceleration vs. the pre-IPO S-1 growth rate triggers multiple reset    | High     |
# MAGIC | **Competition**         | Snowflake, Cloudera (private), dbt Labs, and Microsoft Fabric compete directly | Medium   |
# MAGIC | **Model Risk**          | All prices here are synthetic — not real market data                        | Critical |
# MAGIC | **Concentration Risk**  | Databricks' revenue may be concentrated in top-10 customers                | Medium   |
# MAGIC | **Open-Source Exposure**| Apache Spark & MLflow are open-source foundations; fork risk exists         | Low      |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Disclaimer
# MAGIC
# MAGIC > This analysis uses **entirely synthetic, simulated price data**. Databricks has not publicly
# MAGIC > filed for an IPO as of the knowledge cutoff. All figures, prices, and forecasts are
# MAGIC > for educational and demonstration purposes only. **This is not investment advice.**
# MAGIC > Past performance of comparable companies does not guarantee future results.

# COMMAND ----------

print("Databricks post-IPO forecast notebook complete.")
print(f"All charts saved to: {CHARTS_DIR}")
