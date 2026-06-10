# Data Guide

<p align="center">
  <img src="../frontend/public/logo.svg" alt="CreditBridge Logo" width="120" />
</p>

This document explains how CreditBridge generates its synthetic training data and how raw AA data signals are transformed into model-ready features.

---

## Why Synthetic Data?

CreditBridge does not ship with real customer data. Synthetic profiles are generated to:

1. Demonstrate the full pipeline without requiring access to actual AA feeds.
2. Provide a reproducible training set with known statistical properties.
3. Allow anyone to run the complete pipeline without data access agreements.

The synthetic generator is calibrated to match real-world distributions from:
- **World Bank Global Findex** — India gender and geography distributions.
- **RBI UPI statistics** — transaction volume and failure rate baselines.
- **Markov chain models** — realistic behavioral sequences for utility and mobile payments.

---

## Synthetic Profile Generation

### Entry point
```powershell
cd backend
python data/synthetic/generate_profiles.py
# Output: data/synthetic/profiles.parquet (80,000 rows)
```

### Profile Schema (`ApplicantProfile` — Pydantic v2)

| Field | Type | Description |
|-------|------|-------------|
| `applicant_id` | str | Unique ID: `IND-2026-{index:06d}` |
| `gender` | `"M"` or `"F"` | 52% M / 48% F (Findex calibrated) |
| `geography` | `"urban"` / `"semi-urban"` / `"rural"` | 30% / 35% / 35% |
| `income_proxy` | `"high"` / `"mid"` / `"low"` | 20% / 50% / 30% |
| `is_msme` | bool | 20% true (MSME / small business) |
| `upi_count` | `List[int]` (12 months) | Monthly UPI transaction counts |
| `upi_failed_count` | `List[int]` (12 months) | Monthly UPI failure counts |
| `upi_amount` | `List[float]` (12 months) | Monthly UPI transaction totals (INR) |
| `upi_merchant_count` | `List[int]` (12 months) | Monthly distinct merchant count |
| `upi_night_count` | `List[int]` (12 months) | Night-hour transactions per month |
| `upi_income_deposits` | `List[int]` (12 months) | Salary/income deposits detected |
| `utility_status` | `List[str]` (12 months) | `"on_time"` / `"late"` / `"lapsed"` |
| `utility_days_late` | `List[float]` (12 months) | Days relative to due date |
| `mobile_recharge_status` | `List[str]` (12 months) | `"on_time"` / `"late"` / `"lapsed"` |
| `mobile_plan_value` | `List[float]` (12 months) | Monthly recharge value (INR) |
| `gst_status` | `List[str]` (12m or empty) | `"filed"` / `"late"` / `"unfiled"` |
| `gst_turnover` | `List[float]` (12m or empty) | Monthly GST turnover (INR) |
| `gst_penalties` | `List[float]` (12m or empty) | Monthly GST penalty amount (INR) |
| `income_shock_job_loss` | bool | Random job loss event (~8% rate) |
| `income_shock_health` | bool | Random health shock event (~5% rate) |
| `default_label` | `0` or `1` | Synthetic ground truth |

### Generation Logic

**UPI signals**: Base transaction volume is drawn from a `Beta(3, 2)` distribution, scaled by income level (1.8× for high, 1.0× for mid, 0.5× for low). Monthly counts follow a Poisson distribution around this base. Failure rates are 4% for low-risk profiles and 12% for high-risk profiles, with added noise.

**Utility & Mobile payment sequences**: Generated using a **3-state Markov chain**:
- States: `on_time` → `late` → `lapsed`
- Two transition matrices: one for "good" profiles (high probability of staying `on_time`), one for "risky" profiles (higher probability of degrading to `lapsed`).

**GST (MSME only)**: Filed vs. late vs. unfiled using a Markov chain similar to utility. Turnover values are drawn from income-calibrated log-normal distributions.

**Default label**: Constructed from a log-odds risk score:
```
base_risk = {high: -5.0, mid: -3.5, low: -2.0}

+1.8  if income_shock_job_loss
+1.2  if income_shock_health
+0.6  per utility lapse month
+0.2  per utility late month
+0.4  per mobile lapse month
+1.0  if UPI failure rate > 10%
+0.8  per GST unfiled month (MSME only)

default_probability = sigmoid(risk_score)
default_label ~ Bernoulli(default_probability)
```

This produces an overall default rate of approximately **15–25%**, consistent with real-world unsecured lending portfolios in India's informal economy.

---

## Feature Engineering Pipeline

### Entry point
```powershell
cd backend
python -m src.features.build_features
# Input:  data/synthetic/profiles.parquet
# Output: data/processed/features.parquet
```

### Key step: `expand_list_columns`

The Parquet file stores 12-month signals as native list columns (one cell = Python list of 12 elements). The feature transform functions (`upi_features.py`, etc.) expect individual monthly columns named `{signal}_m{1..12}`.

`expand_list_columns` in `src/features/build_features.py` performs this expansion:

```python
for col in list_cols_to_expand:
    expanded = pd.DataFrame(df[col].tolist(), index=df.index)
    expanded.columns = [f"{col}_m{i}" for i in range(1, 13)]
    df = pd.concat([df, expanded], axis=1)
```

This same function is called in `api/routers/score.py` on every incoming API request, ensuring the same transforms apply to both batch training and online inference.

### UPI Feature Engineering (`src/features/upi_features.py`)

Operates on columns `upi_count_m7` through `upi_count_m12` (the most recent 6 months of each signal).

| Feature | Formula |
|---------|---------|
| `upi_txn_count_6m` | `sum(upi_count_m7..m12)` |
| `upi_consistency_score` | `1 / (1 + std(upi_count_m7..m12))` |
| `upi_merchant_diversity` | `sum(upi_merchant_count_m7..m12) / upi_txn_count_6m` |
| `upi_failed_rate` | `sum(upi_failed_count_m7..m12) / upi_txn_count_6m` |
| `upi_avg_txn_value` | `sum(upi_amount_m7..m12) / upi_txn_count_6m` |
| `upi_night_txn_share` | `sum(upi_night_count_m7..m12) / upi_txn_count_6m` |
| `upi_income_regularity` | `count(upi_income_deposits_m7..m12 >= 1) / 6` |

### Utility Feature Engineering (`src/features/utility_features.py`)

Operates on all 12 months of utility data.

| Feature | Formula |
|---------|---------|
| `utility_streak_length` | Max consecutive `"on_time"` months across m1–m12 |
| `utility_days_before_due_avg` | `mean(utility_days_late_m7..m12)` |
| `utility_lapse_count_12m` | `count(utility_status_m1..m12 == "lapsed")` |
| `utility_reinstatement_count` | Count of transitions `"lapsed" → "on_time"/"late"` across m1–m12 |

### Mobile Feature Engineering (`src/features/mobile_features.py`)

| Feature | Formula |
|---------|---------|
| `mobile_plan_tier` | `1` if m12 value ≤ 200 INR; `2` if ≤ 500 INR; `3` if > 500 INR |
| `mobile_recharge_streak` | Max consecutive `"on_time"` recharges across m1–m12 |
| `mobile_plan_trend` | `mean(m7..m12 value) / mean(m1..m6 value)` |
| `mobile_lapse_count` | `count(mobile_recharge_status_m1..m12 == "lapsed")` |

### GST Feature Engineering (`src/features/gst_features.py`)

For non-MSME applicants, GST features are **imputed** with neutral values (12, 1.0, 0.0) that have zero effect on the model prediction.

| Feature | MSME Formula | Non-MSME |
|---------|-------------|---------|
| `gst_filing_regularity` | `count("filed" in gst_status list)` | 12 |
| `gst_turnover_trend` | `mean(gst_turnover[9:12]) / mean(gst_turnover[6:9])` | 1.0 |
| `gst_penalty_count` | `sum(gst_penalties list)` | 0.0 |

### Final Feature Matrix

After all transforms, the pipeline retains exactly 24 columns:

```
applicant_id, gender, geography, income_proxy, is_msme,
upi_txn_count_6m, upi_consistency_score, upi_merchant_diversity,
upi_failed_rate, upi_avg_txn_value, upi_night_txn_share, upi_income_regularity,
utility_streak_length, utility_days_before_due_avg, utility_lapse_count_12m, utility_reinstatement_count,
mobile_plan_tier, mobile_recharge_streak, mobile_plan_trend, mobile_lapse_count,
gst_filing_regularity, gst_turnover_trend, gst_penalty_count,
default_label
```

Null values are filled with `0` before saving to avoid silent NaN propagation in XGBoost.
