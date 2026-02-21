import os
import random
from datetime import date, timedelta
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")

random.seed(42)
np.random.seed(42)

START_DATE = date(2024, 1, 1)
END_DATE = date(2026, 2, 20)

def ensure_dirs():
    os.makedirs(RAW_DIR, exist_ok=True)

def build_asset_universe():
    """
    Small, realistic asset universe.
    Keep it manageable for a portfolio project, but large enough to feel real.
    """
    equities = ["AAPL", "MSFT", "AMZN", "GOOGL", "NVDA", "META", "JPM", "V", "UNH", "HD",
                "COST", "PEP", "KO", "TMO", "CRM", "ADBE", "NFLX", "ORCL", "INTC", "CSCO"]
    bonds = ["IEF", "TLT", "AGG", "BND", "LQD", "HYG"]
    cash = ["CASH"]  # constant $1 price

    rows = []
    for t in equities:
        rows.append({"ticker": t, "asset_class": "Equity"})
    for t in bonds:
        rows.append({"ticker": t, "asset_class": "Bonds"})
    for t in cash:
        rows.append({"ticker": t, "asset_class": "Cash"})

    return pd.DataFrame(rows)

def date_range(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)

def generate_prices(assets_df: pd.DataFrame):
    """
    Generate daily close prices using a simple geometric random walk.
    Not financial-grade, but realistic enough for drift/valuation behavior.
    """
    tickers = assets_df["ticker"].tolist()

    # Start prices (reasonable ranges)
    start_prices = {}
    for t in tickers:
        if t == "CASH":
            start_prices[t] = 1.0
        elif t in ["TLT", "IEF", "AGG", "BND", "LQD", "HYG"]:
            start_prices[t] = float(np.random.uniform(80, 140))
        else:
            start_prices[t] = float(np.random.uniform(50, 400))

    # Daily vol assumptions
    # equities higher vol, bonds lower, cash constant
    vol = {}
    for t in tickers:
        if t == "CASH":
            vol[t] = 0.0
        elif t in ["TLT", "IEF", "AGG", "BND", "LQD", "HYG"]:
            vol[t] = 0.004   # ~0.4% daily std
        else:
            vol[t] = 0.012   # ~1.2% daily std

    rows = []
    current = start_prices.copy()

    for d in date_range(START_DATE, END_DATE):
        for t in tickers:
            if t == "CASH":
                price = 1.0
            else:
                # random walk with small drift
                shock = np.random.normal(loc=0.0002, scale=vol[t])
                current[t] = max(0.5, current[t] * (1.0 + shock))
                price = float(round(current[t], 4))

            rows.append({"date": d.isoformat(), "ticker": t, "close_price": price})

    return pd.DataFrame(rows)

def generate_holdings(portfolios_path: str, assets_df: pd.DataFrame, n_min=5, n_max=12):
    """
    Create holdings per portfolio: 5–12 tickers.
    Quantities assigned so portfolio values are in a plausible range.
    """
    portfolios = pd.read_csv(portfolios_path)
    tickers_by_class = {
        "Equity": assets_df[assets_df.asset_class == "Equity"]["ticker"].tolist(),
        "Bonds":  assets_df[assets_df.asset_class == "Bonds"]["ticker"].tolist(),
        "Cash":   ["CASH"],
    }

    rows = []
    for _, p in portfolios.iterrows():
        pid = p["portfolio_id"]

        # decide number of holdings
        n = random.randint(n_min, n_max)

        # ensure mix: at least 1 bond, 1 equity, plus maybe cash
        equity_count = max(1, int(n * 0.6))
        bond_count = max(1, int(n * 0.3))
        cash_count = 1 if random.random() < 0.7 else 0

        chosen = set()
        chosen.update(random.sample(tickers_by_class["Equity"], k=min(equity_count, len(tickers_by_class["Equity"]))))
        chosen.update(random.sample(tickers_by_class["Bonds"], k=min(bond_count, len(tickers_by_class["Bonds"]))))
        if cash_count:
            chosen.add("CASH")

        # if still short, fill from equities
        while len(chosen) < n:
            chosen.add(random.choice(tickers_by_class["Equity"]))

        # assign quantities (roughly scale portfolios)
        # equities: 5–80 shares, bonds ETFs: 10–200 shares, cash: 500–20000 units ($)
        for t in chosen:
            asset_class = assets_df.loc[assets_df.ticker == t, "asset_class"].iloc[0]
            if asset_class == "Equity":
                qty = int(np.random.uniform(5, 80))
            elif asset_class == "Bonds":
                qty = int(np.random.uniform(10, 200))
            else:
                qty = float(round(np.random.uniform(500, 20000), 2))

            rows.append({
                "portfolio_id": pid,
                "ticker": t,
                "asset_class": asset_class,
                "quantity": qty
            })

    return pd.DataFrame(rows)

def main():
    ensure_dirs()

    assets = build_asset_universe()
    assets_path = os.path.join(RAW_DIR, "assets_universe.csv")
    assets.to_csv(assets_path, index=False)

    portfolios_path = os.path.join(RAW_DIR, "portfolios_raw.csv")
    holdings = generate_holdings(portfolios_path, assets)
    holdings_path = os.path.join(RAW_DIR, "holdings_raw.csv")
    holdings.to_csv(holdings_path, index=False)

    prices = generate_prices(assets)
    prices_path = os.path.join(RAW_DIR, "prices_raw.csv")
    prices.to_csv(prices_path, index=False)

    print(f"✅ Wrote asset universe: {assets_path} ({len(assets):,} tickers)")
    print(f"✅ Wrote holdings: {holdings_path} ({len(holdings):,} rows)")
    print(f"✅ Wrote prices: {prices_path} ({len(prices):,} rows for {prices['date'].nunique():,} days)")

if __name__ == "__main__":
    main()