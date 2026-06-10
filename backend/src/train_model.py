import pandas as pd
import numpy as np
import os
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import joblib

def train_xgboost(input_path="data/processed/features.csv", model_dir="models/"):
    print(f"Loading features from {input_path}...")
    df = pd.read_csv(input_path)
    
    features = [
        "age", "income", "location_tier", 
        "upi_tx_count_6m", "upi_tx_volume_6m", "upi_avg_tx_size_6m",
        "upi_tx_count_12m", "upi_tx_volume_12m", "upi_avg_tx_size_12m",
        "upi_tx_velocity",
        "utility_on_time_6m", "utility_delayed_6m",
        "utility_on_time_ratio_6m", "utility_delayed_ratio_6m",
        "mobile_recharge_avg_amount_6m", "mobile_recharge_days_since_last",
        "mobile_recharge_consistency",
        "is_business", "gst_filing_regularity", "is_active_business",
        "risk_score_proxy"
    ]
    
    target = "default_flag"
    
    X = df[features]
    y = df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("Setting up monotone constraints...")
    # Monotone constraints: 1 (increasing), -1 (decreasing), 0 (no constraint)
    # Target is default_flag (1 = default, 0 = no default)
    # So features that reduce risk should have -1, features that increase risk should have 1
    monotone_constraints = {
        "income": -1,
        "upi_tx_count_6m": -1,
        "upi_tx_volume_6m": -1,
        "utility_on_time_ratio_6m": -1,
        "utility_delayed_ratio_6m": 1,
        "mobile_recharge_days_since_last": 1,
        "is_active_business": -1,
        "risk_score_proxy": 1
    }
    
    # Map dictionary to tuple for XGBoost (based on exact feature order)
    constraints_tuple = tuple(monotone_constraints.get(col, 0) for col in features)
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        objective="binary:logistic",
        monotone_constraints=constraints_tuple,
        random_state=42
    )
    
    print("Training XGBoost classifier...")
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"Validation AUC: {auc:.4f}")
    
    # Save model
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "xgb_model.joblib")
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")
    
    return model

if __name__ == "__main__":
    train_xgboost()
