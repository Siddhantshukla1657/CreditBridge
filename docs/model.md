# Model Reference

<p align="center">
  <img src="../frontend/public/logo.svg" alt="CreditBridge Logo" width="120" />
</p>

This document covers the CreditBridge ML model — how it was designed, what features it uses, how it was trained, and what performance it achieves.

---

## Model Design Principles

CreditBridge is a **binary classification** model predicting the probability that a given applicant will default on a loan in the next 12 months (`default_label = 1`). Three design principles guided every technical choice:

1. **Monotonicity by design** — higher UPI consistency should never increase predicted default risk. XGBoost's built-in monotone constraints enforce this, making the model's behavior intuitive and auditable.
2. **Calibrated probabilities** — raw XGBoost outputs are overconfident. Platt scaling on a held-out validation set produces calibrated probability estimates suitable for score banding.
3. **Fairness as a first-class metric** — Aequitas demographic audits run as part of the training loop, not as an afterthought.

---

## Feature Set (18 Features)

### Demographics (8 features — one-hot encoded)

| Feature | Type | Meaning |
|---------|------|---------|
| `gender_M` | Binary | 1 if applicant is male |
| `geography_urban` | Binary | 1 if urban location |
| `geography_semi_urban` | Binary | 1 if semi-urban location |
| `geography_rural` | Binary | 1 if rural location |
| `income_high` | Binary | 1 if high income proxy |
| `income_mid` | Binary | 1 if mid income proxy |
| `income_low` | Binary | 1 if low income proxy |
| `is_msme_int` | Binary | 1 if MSME / small business |

> These features carry **no monotone constraint** — their correlation with default varies and must be learned freely.

### UPI Features (7 features)

| Feature | Computation | Monotone Constraint |
|---------|-------------|---------------------|
| `upi_txn_count_6m` | Sum of monthly UPI transaction counts (m7–m12) | — |
| `upi_consistency_score` | `1 / (1 + std_dev(monthly_counts))` — closer to 1 means more consistent | `-1` (higher → lower default risk) |
| `upi_merchant_diversity` | `sum(merchants) / sum(transactions)` | — |
| `upi_failed_rate` | `sum(failed) / sum(transactions)` | `+1` (higher → higher default risk) |
| `upi_avg_txn_value` | `sum(amount) / sum(transactions)` | — |
| `upi_night_txn_share` | `sum(night_txns) / sum(transactions)` | — |
| `upi_income_regularity` | Fraction of 6 months with ≥ 1 income deposit | `-1` |

### Utility Payment Features (4 features)

| Feature | Computation | Monotone Constraint |
|---------|-------------|---------------------|
| `utility_streak_length` | Longest consecutive "on_time" payment streak (12m) | `-1` |
| `utility_days_before_due_avg` | Average days relative to due date; negative = paid early | `+1` (later payment → higher risk) |
| `utility_lapse_count_12m` | Count of "lapsed" status months (12m) | `+1` |
| `utility_reinstatement_count` | Count of "lapsed → on_time/late" transitions (12m) | — |

### Mobile Recharge Features (4 features)

| Feature | Computation | Monotone Constraint |
|---------|-------------|---------------------|
| `mobile_plan_tier` | 1=low (≤200 INR), 2=mid (201–500 INR), 3=high (>500 INR) | — |
| `mobile_recharge_streak` | Longest consecutive "on_time" recharge streak (12m) | `-1` |
| `mobile_plan_trend` | avg(m7–m12 value) / avg(m1–m6 value) | — |
| `mobile_lapse_count` | Count of "lapsed" recharge months (12m) | `+1` |

### GST / MSME Features (3 features — imputed for non-MSMEs)

| Feature | Computation | Non-MSME Imputation |
|---------|-------------|---------------------|
| `gst_filing_regularity` | Count of "filed" months in 12m | 12 (perfect filer, no GST obligation) |
| `gst_turnover_trend` | avg(Q4 turnover) / avg(Q3 turnover) | 1.0 (stable) |
| `gst_penalty_count` | Sum of penalty values in 12m | 0.0 |

---

## Training Setup

### Data Split

```
80,000 profiles (70% / 15% / 15%)
├── Train set:      55,998 rows → SMOTE oversampling
├── Validation set: 12,002 rows → Platt calibration fitting
└── Test set:       12,000 rows → final metric evaluation
```

### Class Imbalance

The synthetic dataset has a natural default rate of approximately **15–20%**. This imbalance is corrected with **SMOTE** (Synthetic Minority Over-sampling Technique), which generates synthetic minority-class (default) examples by interpolating between existing ones in feature space. After SMOTE, the training set is class-balanced.

### XGBoost Hyperparameters (`configs/train_config.yaml`)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `n_estimators` | 500 | Sufficient trees for convergence with early stopping |
| `max_depth` | 6 | Captures feature interactions without overfitting |
| `learning_rate` | 0.05 | Conservative step size with 500 trees |
| `subsample` | 0.8 | Row subsampling reduces variance |
| `colsample_bytree` | 0.8 | Feature subsampling reduces variance |
| `eval_metric` | `auc` | Used for early stopping on validation set |

### Monotone Constraints

XGBoost's `monotone_constraints` parameter enforces that the model's predictions are monotonically increasing or decreasing with respect to specific features. For example:

- `upi_consistency_score` has constraint `-1`: as consistency increases, the predicted default probability must decrease. This mirrors business intuition and prevents the model from learning spurious inverse relationships from noise.

### Platt Calibration

After training, the XGBoost model is wrapped in `FrozenEstimator` (sklearn 1.6+) to prevent re-fitting, then passed to `CalibratedClassifierCV(method="sigmoid")`. The calibration mapping is fitted on the held-out validation set (`X_val`, `y_val`). The resulting calibrated probability is what flows into the scoring formula.

**Why calibration matters**: raw XGBoost probabilities can be systematically biased (often overconfident). Calibrated probabilities represent genuine likelihoods — a predicted probability of 0.2 should mean approximately 20% of such applicants actually default.

### Score Mapping

The calibrated default probability `p` is mapped to the 300–900 credit score scale:

```
score = round(900 - (p × 600))

p = 0.0 → score = 900 (Prime)
p = 0.5 → score = 600 (Subprime boundary)
p = 1.0 → score = 300 (Decline)
```

Confidence is `1 - abs(p - 0.5) * 2`, representing how decisively the model placed the applicant on one side of the 0.5 boundary.

---

## Model Performance

Results from training on 80K synthetic profiles:

| Metric | Target | Achieved |
|--------|--------|----------|
| AUC (ROC) | ≥ 0.88 | **0.9243** ✅ |
| KS Statistic | ≥ 0.40 | **0.7008** ✅ |
| ECE (Expected Calibration Error) | ≤ 0.04 | **0.0302** ✅ |
| Brier Score | < 0.15 | **0.0998** ✅ |

### AUC (0.9243)
Area under the ROC curve. An AUC of 0.92 means the model correctly ranks a random defaulter above a random non-defaulter 92.4% of the time.

### KS Statistic (0.7008)
Kolmogorov-Smirnov statistic: the maximum separation between the cumulative distribution of predicted scores for defaulters vs. non-defaulters. At 0.70, the score distributions are highly discriminating.

### ECE (0.0302)
Expected Calibration Error: the average gap between predicted probability and actual default rate across score buckets. An ECE of 0.03 means predicted probabilities are within 3 percentage points of true rates on average — well within the ≤ 0.04 target.

---

## Explainability — SHAP

Every score response includes a SHAP (SHapley Additive exPlanations) breakdown computed via `shap.TreeExplainer` applied to the **base model** (not the calibrated wrapper).

The waterfall data included in the API response shows:
- `base_value`: the model's average prediction in log-odds space.
- Per-feature SHAP values: each feature's contribution (positive = increases default risk = lowers score, negative = decreases default risk = raises score).

SHAP values are converted to **plain-language reasons** by `reason_generator.py`. The top 3 factors (by absolute SHAP magnitude) are converted to human-readable sentences following the RBI Fair Practice Code format:

> *"Your UPI transaction consistency over the last 6 months has positively contributed to your score."*

---

## Fairness Auditing — Aequitas

After test-set evaluation, the model's predictions are passed through Aequitas to check for demographic disparities across:

- **Gender**: M vs. F
- **Geography**: urban vs. semi-urban vs. rural  
- **Income proxy**: high vs. mid vs. low

Metrics checked:
- **FPR Parity** (False Positive Rate) — are certain groups disproportionately denied credit?
- **Equal Opportunity** (True Positive Rate) — are creditworthy applicants in certain groups being missed?

The disparity threshold is **10%** — if any group's metric exceeds the reference group's by more than 10%, a violation is flagged. Results are saved to `models/fairness_report.json`.

---

## Experiment Tracking — MLflow

All training runs are logged to MLflow under the experiment `CreditBridge-Alternative-Scoring`. Each run records:

- XGBoost hyperparameters
- SMOTE configuration
- AUC, KS, ECE, Brier Score
- Fairness audit pass/fail flag
- Serialized model artifact
- Reliability curve plot

To view the MLflow UI:
```powershell
cd backend
mlflow ui
# → http://localhost:5000
```
