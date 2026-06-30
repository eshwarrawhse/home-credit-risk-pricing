"""
Risk-Based Loan Pricing Analysis
----------------------------------
Input: application_train.csv (Home Credit Default Risk dataset, Kaggle)
Output: risk tiers, default rate per tier, flat vs tiered pricing revenue comparison, 3 charts

Run: python scripts/risk_pricing_analysis.py
Requires: pandas, numpy, scikit-learn, matplotlib
Install: pip install -r requirements.txt
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import os

# ---------- 1. LOAD ----------
DATA_PATH = r'data/application_train.csv'  # place the Kaggle CSV here
df = pd.read_csv(DATA_PATH)
print(f"Loaded {len(df):,} rows, {df.shape[1]} columns")
print(f"Default rate (TARGET=1): {df['TARGET'].mean():.2%}")

# ---------- 2. SELECT FEATURES ----------
# Simple and explainable on purpose — this is a pricing story, not a model-accuracy contest
features = [
    "AMT_INCOME_TOTAL",      # annual income
    "AMT_CREDIT",            # loan amount
    "AMT_ANNUITY",           # loan annuity (repayment per period)
    "DAYS_BIRTH",            # age in negative days
    "DAYS_EMPLOYED",         # employment length in negative days (has anomalies, see below)
    "CNT_CHILDREN",
    "CNT_FAM_MEMBERS",
]

data = df[features + ["TARGET"]].copy()

# Fix known anomaly: DAYS_EMPLOYED has a placeholder value of 365243 for unemployed/pensioners
data["DAYS_EMPLOYED"] = data["DAYS_EMPLOYED"].replace(365243, np.nan)

data["AGE_YEARS"] = -data["DAYS_BIRTH"] / 365
data["EMPLOYED_YEARS"] = -data["DAYS_EMPLOYED"] / 365

# Engineered ratios — real underwriting signals
data["CREDIT_INCOME_RATIO"] = data["AMT_CREDIT"] / data["AMT_INCOME_TOTAL"]
data["ANNUITY_INCOME_RATIO"] = data["AMT_ANNUITY"] / data["AMT_INCOME_TOTAL"]

model_features = [
    "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY",
    "AGE_YEARS", "EMPLOYED_YEARS", "CNT_CHILDREN", "CNT_FAM_MEMBERS",
    "CREDIT_INCOME_RATIO", "ANNUITY_INCOME_RATIO",
]

data = data.dropna(subset=model_features)
print(f"\nAfter cleaning: {len(data):,} rows remain")

X = data[model_features]
y = data["TARGET"]

# ---------- 3. TRAIN A SIMPLE, EXPLAINABLE MODEL ----------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

clf = LogisticRegression(max_iter=1000, class_weight="balanced")
clf.fit(X_train_scaled, y_train)

auc = roc_auc_score(y_test, clf.predict_proba(X_test_scaled)[:, 1])
print(f"\nModel AUC on test set: {auc:.3f}")
print("(AUC is a sanity check, not the headline metric — this is a pricing story, not a model-accuracy contest)")

# ---------- 4. SCORE THE FULL DATASET & BUILD RISK TIERS ----------
X_scaled_full = scaler.transform(X)
data["default_prob"] = clf.predict_proba(X_scaled_full)[:, 1]

data["risk_tier"] = pd.qcut(
    data["default_prob"], q=5,
    labels=["Tier 1 (Lowest Risk)", "Tier 2", "Tier 3", "Tier 4", "Tier 5 (Highest Risk)"]
)

tier_summary = data.groupby("risk_tier").agg(
    n_loans=("TARGET", "count"),
    actual_default_rate=("TARGET", "mean"),
    avg_predicted_prob=("default_prob", "mean"),
    avg_loan_amount=("AMT_CREDIT", "mean"),
    avg_income=("AMT_INCOME_TOTAL", "mean"),
).round(4)

print("\n" + "=" * 70)
print("RISK TIER VALIDATION — does the segmentation actually separate default behavior?")
print("=" * 70)
print(tier_summary)

# ---------- 5. PRICING SIMULATION: FLAT VS TIERED (ELASTICITY-ADJUSTED) ----------
# ============================================================================
# KEY ASSUMPTION BLOCK
#
# Elasticity assumption (semi-elasticity = % volume change per 1pp rate change
# from the flat baseline). Literature-anchored, not estimated from this dataset.
# A real version would require a pricing A/B test.
#
#   Tier 1: -8%/pt   Tier 2: -10%/pt   Tier 3: -12%/pt
#   Tier 4: -15%/pt  Tier 5: -20%/pt + kink beyond +3pt
#
# POLICY GUARDRAIL: no tier is frozen. Tier 1-2 are expected to land BELOW
# flat (funded by Tier 3-5 above flat). The optimizer alone will never
# discount Tier 1-2 — see Section 5c for why that decision is made explicitly.
# ============================================================================

FLAT_RATE = 0.14

tier_default_rates = tier_summary["actual_default_rate"].to_dict()
tier_avg_credit = tier_summary["avg_loan_amount"].to_dict()
tier_volume = tier_summary["n_loans"].to_dict()

elasticity_pct_per_point = {
    "Tier 1 (Lowest Risk)": -0.08,
    "Tier 2": -0.10,
    "Tier 3": -0.12,
    "Tier 4": -0.15,
    "Tier 5 (Highest Risk)": -0.20,
}
kink_threshold_pts = 3.0
kink_extra_pct_per_point = -0.08
MAX_DISCOUNT_VOLUME_GAIN = 0.30


def surviving_volume_fraction(tier, rate_pts_above_flat):
    base_elasticity = elasticity_pct_per_point[tier]
    effect = base_elasticity * rate_pts_above_flat
    if tier == "Tier 5 (Highest Risk)" and rate_pts_above_flat > kink_threshold_pts:
        extra_pts = rate_pts_above_flat - kink_threshold_pts
        effect += kink_extra_pct_per_point * extra_pts
    survival = 1 + effect
    survival = min(survival, 1 + MAX_DISCOUNT_VOLUME_GAIN)
    return max(survival, 0.05)


def tier_net_revenue(tier, rate):
    rate_pts_above_flat = (rate - FLAT_RATE) * 100
    survival = surviving_volume_fraction(tier, rate_pts_above_flat)
    surviving_loans = tier_volume[tier] * survival
    avg_credit = tier_avg_credit[tier]
    default_rate = tier_default_rates[tier]
    interest_revenue = surviving_loans * avg_credit * rate
    expected_loss = surviving_loans * avg_credit * default_rate
    return interest_revenue - expected_loss, surviving_loans


# Naive v1 (fixed rates, no elasticity) — shown for contrast
naive_tiered_rates = {
    "Tier 1 (Lowest Risk)": 0.10, "Tier 2": 0.12, "Tier 3": 0.14,
    "Tier 4": 0.17, "Tier 5 (Highest Risk)": 0.22,
}

# Elasticity optimizer: per-tier rate that maximises net revenue within +/-5pt of flat
rate_grid = np.arange(FLAT_RATE - 0.05, FLAT_RATE + 0.05 + 0.001, 0.005)

best_rates = {}
for tier in tier_volume:
    best_rev = -np.inf
    best_rate = FLAT_RATE
    for rate in rate_grid:
        rev, _ = tier_net_revenue(tier, rate)
        if rev > best_rev:
            best_rev = rev
            best_rate = rate
    best_rates[tier] = round(best_rate, 4)

print("\n" + "=" * 70)
print("OPTIMAL RATE PER TIER (elasticity-adjusted, +/-5pt band)")
print("=" * 70)
for tier, rate in best_rates.items():
    direction = "DISCOUNT" if rate < FLAT_RATE else ("INCREASE" if rate > FLAT_RATE else "UNCHANGED")
    print(f"{tier:25s}  optimal rate = {rate:.2%}  ({direction}, flat = {FLAT_RATE:.0%})")

# Tier 1-2 retention discount: POLICY decision, not optimizer output.
# The optimizer has no concept of competitive risk (customers poached by a
# rival with sharper pricing). The discount is justified by CLV/retention
# economics and flagged explicitly as an assumption — not a derived number.
TIER_1_2_DISCOUNT_PTS = 1.0
retention_discount_rows = []
for tier in ["Tier 1 (Lowest Risk)", "Tier 2"]:
    discounted_rate = FLAT_RATE - (TIER_1_2_DISCOUNT_PTS / 100)
    rev_at_flat, _ = tier_net_revenue(tier, FLAT_RATE)
    rev_at_discount, surv_loans = tier_net_revenue(tier, discounted_rate)
    cost = rev_at_flat - rev_at_discount
    retention_discount_rows.append({
        "risk_tier": tier,
        "discounted_rate": discounted_rate,
        "year_1_cost": round(cost),
        "surviving_loans_modeled": round(surv_loans),
    })

retention_df = pd.DataFrame(retention_discount_rows).set_index("risk_tier")
print("\n" + "=" * 70)
print(f"TIER 1-2 RETENTION DISCOUNT (POLICY — {TIER_1_2_DISCOUNT_PTS}pt cut, CLV-justified)")
print("=" * 70)
print(retention_df)
print(f"\nTotal year-1 cost of discount: {retention_df['year_1_cost'].sum():,.0f}")

# Final recommended rates: discount on Tier 1-2, optimizer on Tier 3-5
recommended_rates = {}
for tier in tier_volume:
    if tier in ["Tier 1 (Lowest Risk)", "Tier 2"]:
        recommended_rates[tier] = round(FLAT_RATE - (TIER_1_2_DISCOUNT_PTS / 100), 4)
    else:
        recommended_rates[tier] = best_rates[tier]

summary_rows = []
for tier in tier_volume:
    flat_rev, _ = tier_net_revenue(tier, FLAT_RATE)
    naive_rev, _ = tier_net_revenue(tier, naive_tiered_rates[tier])
    rec_rev, _ = tier_net_revenue(tier, recommended_rates[tier])
    summary_rows.append({
        "risk_tier": tier,
        "flat_net_revenue": round(flat_rev),
        "naive_tiered_net_revenue": round(naive_rev),
        "recommended_policy_net_revenue": round(rec_rev),
        "recommended_rate": recommended_rates[tier],
    })

pricing_summary = pd.DataFrame(summary_rows).set_index("risk_tier")
pricing_summary["lift_vs_flat"] = (
    pricing_summary["recommended_policy_net_revenue"] - pricing_summary["flat_net_revenue"]
)

print("\n" + "=" * 70)
print("FULL COMPARISON — flat vs naive-tiered vs recommended policy")
print("=" * 70)
print(pricing_summary)

total_flat = pricing_summary["flat_net_revenue"].sum()
total_naive = pricing_summary["naive_tiered_net_revenue"].sum()
total_recommended = pricing_summary["recommended_policy_net_revenue"].sum()

print(f"\nTOTAL flat-pricing net revenue:          {total_flat:,.0f}")
print(f"TOTAL naive-tiered (v1, no elasticity):  {total_naive:,.0f}  "
      f"({(total_naive - total_flat) / abs(total_flat):+.1%} vs flat)")
print(f"TOTAL recommended-policy net revenue:    {total_recommended:,.0f}  "
      f"({(total_recommended - total_flat) / abs(total_flat):+.1%} vs flat)")

# ---------- 6. SAVE CHARTS ----------
os.makedirs("charts", exist_ok=True)

fig, ax = plt.subplots(figsize=(7, 5))
tier_summary["actual_default_rate"].plot(kind="bar", ax=ax, color="#c0392b")
ax.set_title("Actual Default Rate by Risk Tier")
ax.set_ylabel("Default Rate")
ax.set_xlabel("")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig("charts/01_default_rate_by_tier.png", dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(7, 5))
tier_summary["n_loans"].plot(kind="bar", ax=ax, color="#2980b9")
ax.set_title("Loan Volume by Risk Tier")
ax.set_ylabel("Number of Loans")
ax.set_xlabel("")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig("charts/02_volume_by_tier.png", dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(9, 5))
pricing_summary[["flat_net_revenue", "naive_tiered_net_revenue", "recommended_policy_net_revenue"]].plot(kind="bar", ax=ax)
ax.set_title("Net Revenue by Tier: Flat vs Naive Tiered vs Recommended Policy")
ax.set_ylabel("Net Revenue (Interest minus Expected Loss)")
ax.set_xlabel("")
plt.xticks(rotation=30, ha="right")
plt.legend(["Flat Pricing", "Naive Tiered (v1, no elasticity)", "Recommended Policy"])
plt.tight_layout()
plt.savefig("charts/03_flat_vs_tiered_revenue.png", dpi=150)
plt.close()

print("\nCharts saved to ./charts/")
print("\nDONE.")
