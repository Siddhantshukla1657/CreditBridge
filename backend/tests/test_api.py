import pytest
import os
import tempfile
import sqlite3
import json
import joblib
import numpy as np
from fastapi.testclient import TestClient
from xgboost import XGBClassifier
from sklearn.calibration import CalibratedClassifierCV, FrozenEstimator

from api.main import app
from src.features.upi_features import transform as upi_tf

@pytest.fixture
def test_env_setup():
    # Setup temporary SQLite database
    db_fd, db_path = tempfile.mkstemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    
    # Save a temporary mock model payload
    model_fd, model_path = tempfile.mkstemp()
    os.environ["MODEL_PATH"] = model_path
    
    # Create fake trained model
    X_dummy = np.random.rand(100, 26)
    y_dummy = np.random.choice([0, 1], size=100)
    
    base_model = XGBClassifier(n_estimators=2, max_depth=2, random_state=42)
    base_model.fit(X_dummy, y_dummy)
    
    calibrated_model = CalibratedClassifierCV(estimator=FrozenEstimator(base_model))
    calibrated_model.fit(X_dummy, y_dummy)
    
    feature_cols = [
        "gender_M", "geography_urban", "geography_semi_urban", "geography_rural",
        "income_high", "income_mid", "income_low", "is_msme_int",
        "upi_txn_count_6m", "upi_consistency_score", "upi_merchant_diversity", "upi_failed_rate",
        "upi_avg_txn_value", "upi_night_txn_share", "upi_income_regularity",
        "utility_streak_length", "utility_days_before_due_avg", "utility_lapse_count_12m", "utility_reinstatement_count",
        "mobile_plan_tier", "mobile_recharge_streak", "mobile_plan_trend", "mobile_lapse_count",
        "gst_filing_regularity", "gst_turnover_trend", "gst_penalty_count"
    ]
    
    payload = {
        "base_model": base_model,
        "calibrated_model": calibrated_model,
        "feature_names": feature_cols,
        "metrics": {"auc": 0.90, "ks": 0.45, "ece": 0.02, "brier_score": 0.05},
        "model_version": "1.0.0-test"
    }
    joblib.dump(payload, model_path)
    
    # Clean up and reload lifespan
    yield db_path, model_path
    
    os.close(db_fd)
    os.unlink(db_path)
    os.close(model_fd)
    os.unlink(model_path)



def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

def test_model_card_without_load():
    # Clear client state or load with no model
    # Should return a card stating no model loaded
    with TestClient(app) as client:
        response = client.get("/model-card")
        assert response.status_code == 200
        assert "model_version" in response.json()

def test_score_endpoint(test_env_setup):
    db_path, model_path = test_env_setup
    
    with TestClient(app) as client:
        # Load mock card
        card_res = client.get("/model-card")
        assert card_res.json()["model_version"] == "1.0.0-test"
        
        # Valid payload representing Pydantic model
        applicant_payload = {
            "applicant_id": "IND-TEST-9999",
            "gender": "M",
            "geography": "urban",
            "income_proxy": "high",
            "is_msme": True,
            "upi_count": [10] * 12,
            "upi_failed_count": [0] * 12,
            "upi_amount": [1000.0] * 12,
            "upi_merchant_count": [5] * 12,
            "upi_night_count": [1] * 12,
            "upi_income_deposits": [1] * 12,
            "utility_status": ["on_time"] * 12,
            "utility_days_late": [-3.0] * 12,
            "mobile_recharge_status": ["on_time"] * 12,
            "mobile_plan_value": [399.0] * 12,
            "gst_status": ["filed"] * 12,
            "gst_turnover": [150000.0] * 12,
            "gst_penalties": [0.0] * 12,
            "income_shock_job_loss": False,
            "income_shock_health": False
        }
        
        score_res = client.post("/score", json=applicant_payload)
        assert score_res.status_code == 200
        
        data = score_res.json()
        assert data["applicant_id"] == "IND-TEST-9999"
        assert 300 <= data["score"] <= 900
        assert "band" in data
        assert "default_probability" in data
        assert "waterfall_data" in data
        assert len(data["top_factors"]) <= 3
        
        # Query score retrieval from cache
        get_res = client.get("/score/IND-TEST-9999")
        assert get_res.status_code == 200
        assert get_res.json()["score"] == data["score"]
