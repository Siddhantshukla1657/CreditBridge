# Backend Guide

<p align="center">
  <img src="../frontend/public/logo.svg" alt="CreditBridge Logo" width="120" />
</p>

The CreditBridge backend is a Python monorepo containing the full ML pipeline — data generation, feature engineering, model training, SHAP explainability, fairness auditing — and a FastAPI REST server that serves scored results in real time.

All backend code lives under **`backend/`** in the repository root.

---

## Directory Structure

```
backend/
├── api/                        # FastAPI application
│   ├── __init__.py
│   ├── main.py                 # App factory, lifespan, CORS, /health
│   ├── schemas.py              # Pydantic v2 request & response models
│   └── routers/
│       └── score.py            # POST /score  GET /score/{id}  GET /model-card
│
├── src/                        # Core ML pipeline
│   ├── features/
│   │   ├── build_features.py   # Pipeline orchestrator (expand + transform + save)
│   │   ├── upi_features.py     # 7 UPI signal features
│   │   ├── utility_features.py # 4 utility payment features
│   │   ├── mobile_features.py  # 4 mobile recharge features
│   │   └── gst_features.py     # 3 GST / MSME features
│   │
│   ├── model/
│   │   ├── train.py            # SMOTE + XGBoost + calibration + MLflow logging
│   │   ├── calibrate.py        # Platt scaling helper (FrozenEstimator pattern)
│   │   ├── predict.py          # Probability → score → band → confidence
│   │   └── evaluate.py         # AUC, KS, ECE, Brier Score + reliability curve
│   │
│   ├── explainability/
│   │   ├── shap_explainer.py   # SHAP TreeExplainer wrapper + waterfall data
│   │   └── reason_generator.py # SHAP → plain-English RBI-compliant reasons
│   │
│   └── fairness/
│       └── audit.py            # Aequitas wrapper — demographic parity checks
│
├── data/
│   ├── synthetic/
│   │   ├── generate_profiles.py # 80K Markov-chain synthetic profiles
│   │   └── profiles.parquet     # Generated data (gitignored)
│   └── processed/
│       └── features.parquet     # Feature-engineered output (gitignored)
│
├── models/
│   ├── xgb_v1.pkl              # Serialized calibrated model + metadata
│   ├── fairness_report.json    # Aequitas audit output
│   └── reliability_curve.png  # Calibration plot
│
├── tests/                      # pytest test suites
│   ├── test_data_generation.py
│   ├── test_features.py
│   ├── test_model.py
│   └── test_api.py
│
├── configs/
│   └── train_config.yaml       # All hyperparameters, paths, fairness config
│
├── requirements.txt
├── Dockerfile
├── .env.dev
└── .env.prod
```

---

## Running the Backend Locally

> **All commands must be run from the `backend/` directory.**

### 1. Set up the virtual environment (once)

```powershell
# From repo root
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 2. Run the full ML pipeline

```powershell
cd backend

# Generate 80K synthetic credit profiles
python data/synthetic/generate_profiles.py

# Run feature engineering pipeline → data/processed/features.parquet
python -m src.features.build_features

# Train XGBoost + calibration + fairness audit → models/xgb_v1.pkl
python -m src.model.train
```

### 3. Start the API server

```powershell
cd backend
uvicorn api.main:app --reload --port 8000
```

The API is now available at:
- **Swagger UI**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

### 4. Run tests

```powershell
cd backend
..\.venv\Scripts\pytest
```

---

## Key Modules Explained

### `api/main.py`

The FastAPI entry point. Uses an `asynccontextmanager` lifespan to:
1. Create the SQLite `score_cache` table on first start.
2. Load `models/xgb_v1.pkl` (the calibrated XGBoost model payload) into `app.state`.
3. Load `models/fairness_report.json` into `app.state`.

CORS is configured to allow requests from `http://localhost:5173` (Vite dev server) and `http://localhost:3000`.

### `api/schemas.py`

Pydantic v2 models defining the wire format:

- **`ApplicantInput`** — 19 fields, all monthly signals as 12-element lists (e.g. `upi_count: List[int]`).
- **`ScoreResponse`** — score, band, default probability, confidence, top 3 factors, waterfall data, fairness flags, model version.
- **`FactorItem`** — single SHAP reason: feature name, label, point impact, plain-text explanation.
- **`WaterfallItem`** — a bar segment in the SHAP waterfall chart.

### `api/routers/score.py`

The core scoring endpoint. On each `POST /score` request:
1. Checks the SQLite cache for a repeat applicant ID.
2. Converts the request dict into a DataFrame and runs `expand_list_columns` to flatten list columns into monthly columns (`upi_count_m1`…`upi_count_m12`).
3. Runs UPI → utility → mobile → GST feature transforms.
4. Runs `preprocess_features` to one-hot-encode demographics.
5. Calls `calibrated_model.predict_proba` and maps to score + band.
6. Runs `ShapExplainerWrapper` on the `base_model` to get SHAP values.
7. Converts SHAP to plain-language reasons via `generate_plain_reasons`.
8. Attaches any applicable fairness flags from the pre-loaded audit report.
9. Inserts the result into SQLite and returns `ScoreResponse`.

### `src/features/build_features.py`

Pipeline orchestrator. The crucial `expand_list_columns` function flattens Parquet list columns (e.g. `upi_count` — a Python list of 12 integers stored as a Parquet array) into individual pandas columns `upi_count_m1` through `upi_count_m12`. This expansion step is also called in the API router before feature transforms, so the same transform functions work in both batch and online inference.

### `src/model/train.py`

Full training pipeline:
1. Loads the feature Parquet into a DataFrame.
2. Performs a 70/15/15 stratified split (train/val/test).
3. Applies SMOTE on the training set to address class imbalance (~15% default rate).
4. Trains `XGBClassifier` with monotone constraints (e.g. higher income → always lower predicted default risk).
5. Wraps the fitted model in `FrozenEstimator` and applies Platt scaling (sigmoid calibration) on the validation set.
6. Evaluates on the test set: AUC, KS, ECE, Brier Score.
7. Runs the Aequitas fairness audit across gender, geography, and income proxy.
8. Logs everything to MLflow and serializes the full payload to `models/xgb_v1.pkl`.

---

## Configuration (`configs/train_config.yaml`)

| Section | Key | Description |
|---------|-----|-------------|
| `data` | `num_profiles` | Number of synthetic profiles to generate |
| `data` | `synthetic_output_path` | Output path for profiles Parquet |
| `data` | `processed_output_path` | Output path for features Parquet |
| `model` | `xgb_params` | All XGBoost hyperparameters |
| `model` | `monotone_constraints` | Per-feature monotonicity direction |
| `model` | `smote_k_neighbors` | SMOTE k parameter |
| `fairness` | `protected_attributes` | Demographic columns to audit |
| `fairness` | `disparity_threshold` | Max allowed group disparity (default 10%) |
| `fairness` | `reference_groups` | Reference group per attribute |
