import os
import random
from datetime import datetime
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")

random.seed(42)

def ensure_dirs():
    os.makedirs(RAW_DIR, exist_ok=True)

def generate_target_allocations():
    return pd.DataFrame([
        {"risk_profile_name": "Conservative", "target_equity_weight": 0.35, "target_bonds_weight": 0.55, "target_cash_weight": 0.10},
        {"risk_profile_name": "Moderate",      "target_equity_weight": 0.60, "target_bonds_weight": 0.35, "target_cash_weight": 0.05},
        {"risk_profile_name": "Aggressive",    "target_equity_weight": 0.80, "target_bonds_weight": 0.15, "target_cash_weight": 0.05},
    ])

def generate_portfolios(n=2000):
    advisors = [f"Advisor_{i:02d}" for i in range(1, 26)]  # 25 advisors
    risk_profiles = ["Conservative", "Moderate", "Aggressive"]
    weights = [0.30, 0.50, 0.20]  # more realistic distribution

    rows = []
    for i in range(1, n + 1):
        portfolio_id = f"P{i:05d}"
        advisor_name = random.choice(advisors)
        risk_profile = random.choices(risk_profiles, weights=weights, k=1)[0]
        rows.append({
            "portfolio_id": portfolio_id,
            "portfolio_name": f"Client Portfolio {i:05d}",
            "advisor_name": advisor_name,
            "risk_profile_name": risk_profile,
            "base_currency": "USD",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return pd.DataFrame(rows)

def main():
    ensure_dirs()

    portfolios = generate_portfolios(2000)
    targets = generate_target_allocations()

    portfolios_path = os.path.join(RAW_DIR, "portfolios_raw.csv")
    targets_path = os.path.join(RAW_DIR, "target_allocations.csv")

    portfolios.to_csv(portfolios_path, index=False)
    targets.to_csv(targets_path, index=False)

    print(f"✅ Wrote {len(portfolios):,} portfolios to: {portfolios_path}")
    print(f"✅ Wrote target allocations to: {targets_path}")

if __name__ == "__main__":
    main()