# CreditBridge — Project Overview

<p align="center">
  <img src="../frontend/public/logo.svg" alt="CreditBridge Logo" width="120" />
</p>

CreditBridge is a production-grade alternative credit scoring system built for India's 190 million financially active but credit-invisible citizens. These individuals transact daily via UPI, pay utility bills, maintain mobile recharge plans, and (for small businesses) file GST — yet remain invisible to the traditional CIBIL bureau scoring system because they have no formal loan or credit card history.

CreditBridge bridges this gap by extracting creditworthiness signals from these Account Aggregator (AA) data streams, producing a score on the familiar 300–900 scale with full per-applicant explainability and automated demographic fairness auditing.

---

## The Problem

India's credit gap is structural:

- **CIBIL coverage**: ~220 million adults with formal credit history out of ~900 million adults.
- **Alternate economy**: UPI processed 131 billion transactions in FY24. Most of these users have no credit bureau footprint.
- **Regulatory push**: RBI's Account Aggregator framework (2021) enables individuals to consent-share their financial data across institutions — creating the infrastructure for alternative scoring.

Traditional lenders reject applicants without bureau history outright. CreditBridge gives these applicants a scored, explained profile backed by verifiable behavioral data.

---

## How It Works — End-to-End

```
Account Aggregator Data
        │
        ▼
  Feature Engineering          ← 18 signals extracted from 4 data sources
  (UPI · Utility · Mobile · GST)
        │
        ▼
  XGBoost Classifier           ← trained on 80K synthetic profiles
  + SMOTE class balancing      ← corrects for 15% natural default rate
  + Platt Calibration          ← converts raw logits to calibrated probabilities
        │
        ├──▶ Credit Score (300–900)    ← mapped from default probability
        ├──▶ SHAP Explanations         ← per-applicant feature attributions
        ├──▶ Plain-Language Reasons    ← RBI Fair Practice Code compliant text
        └──▶ Fairness Audit (Aequitas) ← demographic disparity checks
                │
                ▼
        FastAPI REST Endpoint
                │
                ▼
        React Dashboard
        ├── Lender View    ← applicant table, filters, score drilldown
        └── Applicant View ← self-service form, live score gauge, tips
```

---

## Score Bands

| Score Range | Band       | Interpretation                     |
|-------------|------------|-------------------------------------|
| 750 – 900   | Prime      | Very low default risk               |
| 650 – 749   | Near-prime | Low risk, suitable for most products|
| 550 – 649   | Subprime   | Moderate risk, higher-rate products |
| 400 – 549   | High risk  | Significant risk, collateral needed |
| 300 – 399   | Decline    | High probability of default         |

---

## Data Sources Used

| Source      | Signals | Examples                                          |
|-------------|---------|---------------------------------------------------|
| UPI         | 7       | Transaction volume, consistency, merchant diversity, failure rate |
| Utility     | 4       | Payment streak, days before/after due, lapse count |
| Mobile      | 4       | Plan tier, recharge streak, plan value trend       |
| GST (MSME)  | 3       | Filing regularity, turnover trend, penalty count   |

For full details on feature engineering, see [data.md](./data.md).

---

## Compliance

| Requirement                         | How CreditBridge Addresses It                         |
|-------------------------------------|-------------------------------------------------------|
| RBI Fair Practice Code              | Every scoring response includes 3 plain-language reasons in the applicant's language of interface |
| Account Aggregator Framework        | Input schema maps directly to AA data categories (UPI, utility, mobile, GST) |
| RBI Digital Lending Guidelines 2022 | Audit trail via SQLite cache, model card endpoint, Aequitas fairness report |

---

## Further Reading

| Document | Description |
|----------|-------------|
| [Backend Guide](./backend.md) | Python project structure, ML pipeline, how to run the API |
| [Frontend Guide](./frontend.md) | React dashboard structure, components, how to run the UI |
| [Model Reference](./model.md) | Feature engineering, training setup, performance metrics |
| [API Reference](./api_reference.md) | All REST endpoints with request/response schemas |
| [Data Guide](./data.md) | Synthetic data generation and feature engineering pipeline |
| [Deployment Guide](./deployment.md) | Local dev, Docker, and production deployment |
