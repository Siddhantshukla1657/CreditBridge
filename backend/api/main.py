from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import joblib
import json
import sqlite3
from api.routers.score import router as score_router

# Database initialization
def init_db(db_url: str):
    db_path = db_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS score_cache (
        id            TEXT PRIMARY KEY,
        score         INTEGER NOT NULL,
        band          TEXT NOT NULL,
        default_prob  REAL NOT NULL,
        confidence    REAL NOT NULL,
        top_factors   TEXT NOT NULL,
        waterfall_data TEXT NOT NULL,
        force_plot_data TEXT,
        fairness_flags TEXT NOT NULL,
        model_version TEXT NOT NULL,
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

# Lifespan manager for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load settings
    app.state.db_url = os.getenv("DATABASE_URL", "sqlite:///./score_cache.db")
    model_path = os.getenv("MODEL_PATH", "models/xgb_v1.pkl")
    fairness_path = os.getenv("FAIRNESS_REPORT_PATH", "models/fairness_report.json")
    
    # Initialize cache DB
    init_db(app.state.db_url)
    
    # Load ML Model
    if os.path.exists(model_path):
        print(f"Lifespan loading model from {model_path}...")
        app.state.model_payload = joblib.load(model_path)
    else:
        print(f"Warning: Model not found at {model_path}. API scoring endpoints will be disabled.")
        app.state.model_payload = None
        
    # Load Fairness Report
    if os.path.exists(fairness_path):
        print(f"Lifespan loading fairness report from {fairness_path}...")
        with open(fairness_path, "r") as f:
            app.state.fairness_report = json.load(f)
    else:
        app.state.fairness_report = None
        
    yield
    # Cleanup on shutdown
    pass

app = FastAPI(
    title="CreditBridge API",
    description="AA-powered alternative credit scoring engine",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(score_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "CreditBridge API"}

