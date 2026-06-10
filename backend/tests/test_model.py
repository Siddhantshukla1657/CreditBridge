import pytest
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.calibration import CalibratedClassifierCV
import os
import shutil

from src.features.build_features import main as run_feature_pipeline
from src.features.upi_features import transform as upi_tf
from src.features.utility_features import transform as util_tf
from src.features.mobile_features import transform as mob_tf
from src.features.gst_features import transform as gst_tf

from src.model.train import preprocess_features
from src.model.predict import probability_to_score, score_to_band, predict_score_details
from src.explainability.shap_explainer import ShapExplainerWrapper
from src.explainability.reason_generator import generate_plain_reasons
from src.fairness.audit import run_fairness_audit, FairnessViolationError

from src.features.build_features import expand_list_columns

@pytest.fixture
def clean_synthetic_data():
    # Make a small synthetic dataset for training test
    np.random.seed(42)
    n = 200
    
    # Demographics
    gender = np.random.choice(["M", "F"], size=n)
    geography = np.random.choice(["urban", "semi-urban", "rural"], size=n)
    income_proxy = np.random.choice(["high", "mid", "low"], size=n)
    is_msme = np.random.choice([True, False], size=n)
    
    # Generate list columns
    upi_count = [[int(np.random.poisson(15)) for _ in range(12)] for _ in range(n)]
    upi_failed_count = [[int(np.random.binomial(c, 0.05)) for c in upi_c] for upi_c in upi_count]
    upi_amount = [[float(c * 150) for c in upi_c] for upi_c in upi_count]
    upi_merchant_count = [[int(c * 0.5) for c in upi_c] for upi_c in upi_count]
    upi_night_count = [[int(c * 0.1) for c in upi_c] for upi_c in upi_count]
    upi_income_deposits = [[1 for _ in range(12)] for _ in range(n)]
    
    utility_status = [["on_time"] * 12 for _ in range(n)]
    utility_days_late = [[-2.0] * 12 for _ in range(n)]
    
    mobile_recharge_status = [["on_time"] * 12 for _ in range(n)]
    mobile_plan_value = [[299.0] * 12 for _ in range(n)]
    
    gst_status = [["filed"] * 12 if m else [] for m in is_msme]
    gst_turnover = [[100000.0] * 12 if m else [] for m in is_msme]
    gst_penalties = [[0.0] * 12 if m else [] for m in is_msme]
    
    default_label = np.random.choice([0, 1], size=n, p=[0.85, 0.15])
    
    df = pd.DataFrame({
        "applicant_id": [f"IND-{i}" for i in range(n)],
        "gender": gender,
        "geography": geography,
        "income_proxy": income_proxy,
        "is_msme": is_msme,
        "upi_count": upi_count,
        "upi_failed_count": upi_failed_count,
        "upi_amount": upi_amount,
        "upi_merchant_count": upi_merchant_count,
        "upi_night_count": upi_night_count,
        "upi_income_deposits": upi_income_deposits,
        "utility_status": utility_status,
        "utility_days_late": utility_days_late,
        "mobile_recharge_status": mobile_recharge_status,
        "mobile_plan_value": mobile_plan_value,
        "gst_status": gst_status,
        "gst_turnover": gst_turnover,
        "gst_penalties": gst_penalties,
        "income_shock_job_loss": [False] * n,
        "income_shock_health": [False] * n,
        "default_label": default_label
    })
    return expand_list_columns(df)

def test_probability_to_score():
    assert probability_to_score(0.0) == 900
    assert probability_to_score(1.0) == 300
    assert probability_to_score(0.5) == 600
    
    assert score_to_band(850) == "Prime"
    assert score_to_band(700) == "Near-prime"
    assert score_to_band(600) == "Subprime"
    assert score_to_band(450) == "High risk"
    assert score_to_band(350) == "Decline"

def test_explainability_pipeline(clean_synthetic_data):
    # Pass features transformation
    df_transformed = clean_synthetic_data.copy()
    df_transformed = upi_tf(df_transformed)
    df_transformed = util_tf(df_transformed)
    df_transformed = mob_tf(df_transformed)
    df_transformed = gst_tf(df_transformed)
    
    df_prep = preprocess_features(df_transformed)
    
    feature_cols = [
        "gender_M", "geography_urban", "geography_semi_urban", "geography_rural",
        "income_high", "income_mid", "income_low", "is_msme_int",
        "upi_txn_count_6m", "upi_consistency_score", "upi_merchant_diversity", "upi_failed_rate",
        "upi_avg_txn_value", "upi_night_txn_share", "upi_income_regularity",
        "utility_streak_length", "utility_days_before_due_avg", "utility_lapse_count_12m", "utility_reinstatement_count",
        "mobile_plan_tier", "mobile_recharge_streak", "mobile_plan_trend", "mobile_lapse_count",
        "gst_filing_regularity", "gst_turnover_trend", "gst_penalty_count"
    ]
    
    X = df_prep[feature_cols]
    y = df_prep["default_label"]
    
    # Train simple XGB model
    model = XGBClassifier(n_estimators=10, max_depth=3, learning_rate=0.1, random_state=42)
    model.fit(X, y)
    
    # Test SHAP explainer
    shap_wrapper = ShapExplainerWrapper(model, feature_cols)
    instance = X.iloc[[0]]
    explanation = shap_wrapper.explain_instance(instance)
    
    assert "base_value" in explanation
    assert "features_shap" in explanation
    assert "waterfall_data" in explanation
    assert len(explanation["features_shap"]) == len(feature_cols)
    
    # Test reasons generation
    reasons = generate_plain_reasons(explanation["features_shap"], top_n=3)
    assert len(reasons) <= 3
    for r in reasons:
        assert "feature" in r
        assert "points" in r
        assert "text" in r

def test_fairness_audit(clean_synthetic_data):
    # Check that audit returns dict and runs cleanly
    df_transformed = clean_synthetic_data.copy()
    df_transformed = upi_tf(df_transformed)
    df_transformed = util_tf(df_transformed)
    df_transformed = mob_tf(df_transformed)
    df_transformed = gst_tf(df_transformed)
    
    n = len(clean_synthetic_data)
    y_true = clean_synthetic_data["default_label"].values
    
    # Fake perfect parity predictions
    y_pred_default = np.zeros(n, dtype=int)
    
    config = {
        "fairness": {
            "protected_attributes": ["gender", "geography"],
            "disparity_threshold": 0.20,
            "reference_groups": {"gender": "M", "geography": "urban"}
        }
    }
    
    temp_report_path = "models/temp_test_fairness_report.json"
    report = run_fairness_audit(df_transformed, y_true, y_pred_default, config, output_path=temp_report_path)
    
    assert os.path.exists(temp_report_path)
    assert "passed" in report
    assert report["passed"] is True
    
    if os.path.exists(temp_report_path):
        os.remove(temp_report_path)
