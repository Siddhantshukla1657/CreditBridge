# API Reference

<p align="center">
  <img src="../frontend/public/logo.svg" alt="CreditBridge Logo" width="120" />
</p>

The CreditBridge API is a FastAPI application that exposes scoring, retrieval, and model introspection endpoints over HTTP. The full interactive OpenAPI documentation is available at **http://localhost:8000/docs** when the server is running.

---

## Base URL

| Environment | Base URL |
|-------------|----------|
| Local dev | `http://localhost:8000` |
| Docker (full stack) | `http://localhost:8000` |
| Production | Configurable via environment |

---

## Authentication

The current version does not require authentication tokens. CORS is configured to allow requests from `http://localhost:5173` and `http://localhost:3000`. In production, restrict `ALLOWED_ORIGINS` to your actual frontend domain.

---

## Endpoints

### `GET /health`

Liveness probe. Returns immediately with no model dependency.

**Response**
```json
{
  "status": "ok",
  "service": "CreditBridge API"
}
```

---

### `GET /model-card`

Returns the currently loaded model's metadata, performance metrics, and fairness audit summary. Safe to call without submitting any applicant data — useful for the landing page model card snapshot.

**Response (model loaded)**
```json
{
  "model_name": "CreditBridge alternative credit scoring model",
  "model_version": "1.0.0",
  "framework": "XGBoost + Platt Calibration",
  "performance_metrics": {
    "AUC": 0.9243,
    "KS_Statistic": 0.7008,
    "Expected_Calibration_Error_ECE": 0.0302,
    "Brier_Score": 0.0998
  },
  "fairness_audit": {
    "passed": false,
    "violations": [...]
  }
}
```

**Response (no model loaded)**
```json
{
  "status": "No model loaded",
  "model_version": "None"
}
```

---

### `POST /score`

Submit an applicant's Account Aggregator signals to receive a credit score with SHAP explanations and fairness flags.

**Request body** (`application/json`)

```json
{
  "applicant_id": "IND-2026-000001",
  "gender": "M",
  "geography": "urban",
  "income_proxy": "high",
  "is_msme": false,
  "upi_count":             [12, 14, 11, 15, 13, 16, 12, 14, 13, 15, 11, 14],
  "upi_failed_count":      [ 0,  1,  0,  0,  1,  0,  0,  0,  0,  1,  0,  0],
  "upi_amount":            [8000, 9500, 7200, 10000, 8800, 9200, 7800, 9100, 8400, 9600, 7500, 9800],
  "upi_merchant_count":    [ 6,  7,  5,  8,  6,  7,  6,  7,  6,  8,  5,  7],
  "upi_night_count":       [ 1,  2,  1,  1,  2,  1,  1,  2,  1,  1,  1,  2],
  "upi_income_deposits":   [ 1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1],
  "utility_status":        ["on_time","on_time","on_time","on_time","on_time","on_time","on_time","on_time","on_time","on_time","on_time","on_time"],
  "utility_days_late":     [-8.0, -5.0, -7.0, -6.0, -9.0, -4.0, -8.0, -5.0, -7.0, -6.0, -9.0, -4.0],
  "mobile_recharge_status":["on_time","on_time","on_time","on_time","on_time","on_time","on_time","on_time","on_time","on_time","on_time","on_time"],
  "mobile_plan_value":     [799.0, 799.0, 799.0, 799.0, 799.0, 799.0, 799.0, 799.0, 799.0, 799.0, 799.0, 799.0],
  "gst_status":            [],
  "gst_turnover":          [],
  "gst_penalties":         [],
  "income_shock_job_loss": false,
  "income_shock_health":   false
}
```

**Field reference**

| Field | Type | Description |
|-------|------|-------------|
| `applicant_id` | string (optional) | Unique ID. Auto-generated as `IND-API-{uuid}` if omitted |
| `gender` | `"M"` or `"F"` | Applicant gender |
| `geography` | `"urban"`, `"semi-urban"`, or `"rural"` | Location tier |
| `income_proxy` | `"high"`, `"mid"`, or `"low"` | Declared income bracket |
| `is_msme` | boolean | Whether applicant is a small/micro business |
| `upi_count` | `int[12]` | Monthly UPI transaction counts (m1 = 12 months ago, m12 = most recent) |
| `upi_failed_count` | `int[12]` | Monthly failed UPI transaction counts |
| `upi_amount` | `float[12]` | Total UPI transaction value per month (INR) |
| `upi_merchant_count` | `int[12]` | Distinct merchants transacted with per month |
| `upi_night_count` | `int[12]` | UPI transactions between 10pm–6am per month |
| `upi_income_deposits` | `int[12]` | Income/salary deposits detected per month |
| `utility_status` | `string[12]` | `"on_time"`, `"late"`, or `"lapsed"` per month |
| `utility_days_late` | `float[12]` | Days relative to due date (negative = paid early) |
| `mobile_recharge_status` | `string[12]` | `"on_time"`, `"late"`, or `"lapsed"` per month |
| `mobile_plan_value` | `float[12]` | Monthly mobile recharge value (INR) |
| `gst_status` | `string[]` | `"filed"`, `"late"`, or `"unfiled"` per month — **empty list if not MSME** |
| `gst_turnover` | `float[]` | Monthly GST turnover (INR) — **empty if not MSME** |
| `gst_penalties` | `float[]` | Monthly GST penalty amounts (INR) — **empty if not MSME** |
| `income_shock_job_loss` | boolean | Self-declared job loss in the period |
| `income_shock_health` | boolean | Self-declared health-related financial shock |

**Response** (`200 OK`)

```json
{
  "applicant_id": "IND-2026-000001",
  "score": 812,
  "band": "Prime",
  "default_probability": 0.0813,
  "confidence": 0.837,
  "top_factors": [
    {
      "feature": "upi_consistency_score",
      "label": "UPI Transaction Consistency",
      "points": 42,
      "text": "Your UPI transaction consistency over the last 6 months has strongly contributed to your score."
    },
    {
      "feature": "utility_streak_length",
      "label": "Utility Payment Streak",
      "points": 31,
      "text": "Your uninterrupted utility bill payment history demonstrates strong financial discipline."
    },
    {
      "feature": "upi_failed_rate",
      "label": "UPI Failure Rate",
      "points": -8,
      "text": "A small number of failed UPI transactions slightly impacted your score."
    }
  ],
  "waterfall_data": [
    { "name": "Base", "value": -2.1, "start": 0.0, "end": -2.1, "is_total": false },
    { "name": "upi_consistency_score", "value": 0.8, "start": -2.1, "end": -1.3, "is_total": false },
    ...
    { "name": "Score", "value": -1.6, "start": 0.0, "end": -1.6, "is_total": true }
  ],
  "fairness_flags": [],
  "model_version": "1.0.0"
}
```

**Response field reference**

| Field | Type | Description |
|-------|------|-------------|
| `applicant_id` | string | Echo of the input (or auto-generated) ID |
| `score` | integer | Credit score on 300–900 scale |
| `band` | string | Credit band label |
| `default_probability` | float | Calibrated probability of default (0–1) |
| `confidence` | float | Model decisiveness (0–1, higher = more certain) |
| `top_factors` | FactorItem[] | Top 3 SHAP reasons, positive and negative |
| `waterfall_data` | WaterfallItem[] | Full SHAP waterfall data for chart rendering |
| `fairness_flags` | string[] | Demographic disparity warnings if applicable |
| `model_version` | string | Loaded model version string |

**Error responses**

| Status | Condition |
|--------|-----------|
| `503 Service Unavailable` | Model not loaded — run `src.model.train` first |
| `400 Bad Request` | Feature engineering error (malformed input or missing fields) |

---

### `GET /score/{applicant_id}`

Retrieve a previously cached score result. Results are persisted in the SQLite `score_cache` table.

**Path parameter**: `applicant_id` — the ID used in the original `POST /score` request.

**Response**: Same `ScoreResponse` schema as `POST /score`.

**Error responses**

| Status | Condition |
|--------|-----------|
| `404 Not Found` | No cached score exists for the provided ID |

---

## Score Cache

All scored results are stored in `backend/score_cache.db` (SQLite). The schema:

```sql
CREATE TABLE score_cache (
    id              TEXT PRIMARY KEY,
    score           INTEGER NOT NULL,
    band            TEXT NOT NULL,
    default_prob    REAL NOT NULL,
    confidence      REAL NOT NULL,
    top_factors     TEXT NOT NULL,      -- JSON array
    waterfall_data  TEXT NOT NULL,      -- JSON array
    fairness_flags  TEXT NOT NULL,      -- JSON array
    model_version   TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Repeat requests for the same `applicant_id` are served from the cache without calling the model again.
