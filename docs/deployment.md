# Deployment Guide

<p align="center">
  <img src="../frontend/public/logo.svg" alt="CreditBridge Logo" width="120" />
</p>

This guide covers running CreditBridge in local development, as a full Docker stack, and considerations for production.

---

## Project Layout

```
creditbridge/
├── backend/      ← Python API, ML pipeline, tests
├── frontend/     ← React dashboard (Vite)
├── docs/         ← This documentation
├── docker-compose.yml
└── README.md
```

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Step 1: Set up the Python environment (once)

Run from the **repository root**:

```powershell
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux
pip install -r backend/requirements.txt
```

The virtual environment is placed at the repository root so both IDE tooling and the backend commands on the `backend/` working directory can share it.

### Step 2: Run the ML pipeline (once, or after config changes)

```powershell
cd backend

# 1. Generate 80K synthetic profiles
python data/synthetic/generate_profiles.py

# 2. Feature engineering
python -m src.features.build_features

# 3. Train, calibrate, audit, and save model
python -m src.model.train
```

Expected output from training:
```
AUC:     0.9243
KS Stat: 0.7008
ECE:     0.0302
Brier:   0.0998
Model payload saved to models/xgb_v1.pkl
```

### Step 3: Start the backend API

```powershell
cd backend
uvicorn api.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Step 4: Start the frontend

In a **new terminal**:

```powershell
cd frontend
npm install    # first time only
npm run dev
```

- Dashboard: http://localhost:5173

The Vite dev server automatically proxies `/score`, `/model-card`, and `/health` to `localhost:8000`, so no CORS issues occur in development.

### Step 5: Run the test suite

```powershell
cd backend
..\.venv\Scripts\pytest          # Windows
# ../.venv/bin/pytest            # Mac/Linux
```

All 12 tests should pass.

---

## Docker — Full Stack

The `docker-compose.yml` at the repo root orchestrates both services:

```powershell
# From repo root
docker-compose up --build
```

| Service | Exposed Port | URL |
|---------|-------------|-----|
| `api` | 8000 | http://localhost:8000 |
| `frontend` | 80 | http://localhost:80 |

### Backend Docker build (`backend/Dockerfile`)

Multi-stage build:
1. **Builder stage**: installs Python packages into `/install` from `requirements.txt`.
2. **Runtime stage**: copies the package tree and application code; starts `uvicorn api.main:app`.

The build context is `./backend`, so the Dockerfile operates relative to the `backend/` directory — no path changes are needed inside the Dockerfile.

### Frontend Docker build (`frontend/Dockerfile`)

Multi-stage build:
1. **Builder stage**: runs `npm run build` to produce static files in `dist/`.
2. **Runtime stage**: `nginx:alpine` serves the `dist/` directory. The `nginx.conf` in `frontend/` handles SPA routing by redirecting all non-file requests to `index.html`.

### Volumes

| Volume | Container Path | Purpose |
|--------|---------------|---------|
| `./backend/models` | `/app/models` | Persist model artifacts across container restarts |
| `./backend/data` | `/app/data` | Persist generated data |

---

## Production Considerations

### 1. Replace SQLite with PostgreSQL

For multi-replica deployments, replace SQLite with PostgreSQL. The `docker-compose.yml` includes a `db` service under the `prod` profile:

```powershell
docker-compose --profile prod up --build
```

Update `DATABASE_URL` in `backend/.env.prod`:
```
DATABASE_URL=postgresql://credituser:creditpass@db:5432/creditbridge
```

### 2. Environment Files

| File | Purpose |
|------|---------|
| `backend/.env.dev` | Local development — SQLite, local model paths |
| `backend/.env.prod` | Production — PostgreSQL, production origins |

Never commit `.env.prod` with real credentials. Use a secrets manager (AWS Secrets Manager, Vault, etc.) in production.

### 3. CORS

Restrict `ALLOWED_ORIGINS` to your production frontend domain:

```
ALLOWED_ORIGINS=https://creditbridge.yourdomain.com
```

### 4. Model Updates

When retraining the model:
1. Run the full pipeline from `backend/`.
2. Replace `backend/models/xgb_v1.pkl` and `backend/models/fairness_report.json`.
3. Restart the API container — the lifespan manager reloads artifacts on startup.

### 5. API Latency

The p95 target is ≤ 300ms per `/score` request. SHAP `TreeExplainer` is the most expensive step (~50–80ms on a 500-tree model). For high-throughput production, consider:
- Pre-computing SHAP for a background batch and caching results.
- Using `shap.Explainer` with `max_evals` limits.
- Horizontal scaling behind a load balancer with shared PostgreSQL cache.

---

## Useful Commands Summary

```powershell
# Backend
cd backend
uvicorn api.main:app --reload --port 8000    # Start API
..\.venv\Scripts\pytest                       # Run tests
mlflow ui                                     # View experiment tracking

# Frontend
cd frontend
npm run dev      # Dev server (http://localhost:5173)
npm run build    # Production build

# Docker
docker-compose up --build                    # Full stack
docker-compose --profile prod up --build     # Full stack with PostgreSQL
docker-compose down                          # Stop
docker-compose down -v                       # Stop + delete volumes
```
