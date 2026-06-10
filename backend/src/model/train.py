import os
import yaml
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
# pyrefly: ignore [missing-import]
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier
import mlflow
import argparse

from src.model.calibrate import fit_calibration
from src.model.evaluate import evaluate_model
from src.model.predict import predict_score_details
from src.fairness.audit import run_fairness_audit, FairnessViolationError

def load_config(config_path="configs/train_config.yaml"):
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}

def preprocess_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Statically converts categorical demographics to integer signals.
    """
    df_out = df.copy()
    
    # Gender M/F
    df_out["gender_M"] = (df_out["gender"] == "M").astype(int)
    
    # Geography
    df_out["geography_urban"] = (df_out["geography"] == "urban").astype(int)
    df_out["geography_semi_urban"] = (df_out["geography"] == "semi-urban").astype(int)
    df_out["geography_rural"] = (df_out["geography"] == "rural").astype(int)
    
    # Income Proxy
    df_out["income_high"] = (df_out["income_proxy"] == "high").astype(int)
    df_out["income_mid"] = (df_out["income_proxy"] == "mid").astype(int)
    df_out["income_low"] = (df_out["income_proxy"] == "low").astype(int)
    
    # is_msme to int
    df_out["is_msme_int"] = df_out["is_msme"].astype(int)
    
    return df_out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/train_config.yaml")
    args = parser.parse_args()
    
    config = load_config(args.config)
    processed_path = config["data"]["processed_output_path"]
    target_col = config["model"]["target"]
    
    print(f"Loading feature matrix from {processed_path}...")
    df = pd.read_parquet(processed_path)
    
    # Preprocess categorical demographics
    df_preprocessed = preprocess_features(df)
    
    # Select feature columns (excluding applicant_id, gender/geo/inc string columns, target)
    feature_cols = [
        "gender_M",
        "geography_urban",
        "geography_semi_urban",
        "geography_rural",
        "income_high",
        "income_mid",
        "income_low",
        "is_msme_int",
        "upi_txn_count_6m",
        "upi_consistency_score",
        "upi_merchant_diversity",
        "upi_failed_rate",
        "upi_avg_txn_value",
        "upi_night_txn_share",
        "upi_income_regularity",
        "utility_streak_length",
        "utility_days_before_due_avg",
        "utility_lapse_count_12m",
        "utility_reinstatement_count",
        "mobile_plan_tier",
        "mobile_recharge_streak",
        "mobile_plan_trend",
        "mobile_lapse_count",
        "gst_filing_regularity",
        "gst_turnover_trend",
        "gst_penalty_count"
    ]
    
    X = df_preprocessed[feature_cols]
    y = df_preprocessed[target_col]
    
    # Stratified three-way split: 70% Train, 15% Val (for Calibration), 15% Test
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.15, stratify=y, random_state=config["model"]["random_state"]
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.1765, stratify=y_train_full, random_state=config["model"]["random_state"]
    ) # 0.1765 * 0.85 = ~0.15 of overall
    
    print(f"Data splits: Train={X_train.shape[0]}, Val={X_val.shape[0]}, Test={X_test.shape[0]}")
    
    # Handle Class Imbalance with SMOTE on Training Set
    print("Oversampling minority default class with SMOTE...")
    smote = SMOTE(k_neighbors=config["model"]["smote_k_neighbors"], random_state=config["model"]["random_state"])
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
    print(f"Resampled training size: {X_train_res.shape[0]} (defaults: {y_train_res.sum()})")
    
    # Monotone constraints mapping
    config_constraints = config["model"]["monotone_constraints"]
    constraints = [config_constraints.get(col, 0) for col in feature_cols]
    
    print("Initializing base XGBClassifier with monotone constraints...")
    xgb_params = config["model"]["xgb_params"]
    xgb_params["monotone_constraints"] = tuple(constraints)
    base_model = XGBClassifier(**xgb_params)
    
    # MLflow Setup
    os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "./mlruns"))
    mlflow.set_experiment("CreditBridge-Alternative-Scoring")
    
    with mlflow.start_run() as run:
        print("Training base XGBoost model...")
        base_model.fit(
            X_train_res, y_train_res,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        # Calibration on Validation Set
        # Since base_model is prefitted, we wrap it in FrozenEstimator
        from sklearn.calibration import CalibratedClassifierCV, FrozenEstimator
        calibrated_model = CalibratedClassifierCV(estimator=FrozenEstimator(base_model), method="sigmoid")
        print("Fitting Platt calibration on validation set...")
        calibrated_model.fit(X_val, y_val)
        
        # Predict on test set
        pred_details = predict_score_details(calibrated_model, X_test)
        y_prob = np.array(pred_details["probabilities"])
        y_pred = (y_prob > 0.50).astype(int)
        
        # Evaluate model metrics
        metrics = evaluate_model(y_test, y_prob)
        
        # Run Aequitas fairness audit
        # We need the original (demographics-rich) dataframe aligned with X_test
        df_test_orig = df.iloc[X_test.index]
        
        audit_passed = True
        try:
            audit_report = run_fairness_audit(df_test_orig, y_test.values, y_pred, config)
        except FairnessViolationError as e:
            print(f"FAIRNESS VIOLATION DETECTED: {e}")
            audit_passed = False
            
        # Log MLflow parameters
        mlflow.log_params(xgb_params)
        mlflow.log_param("smote_k_neighbors", config["model"]["smote_k_neighbors"])
        mlflow.log_param("calibrator_method", "Platt/sigmoid")
        mlflow.log_param("fairness_audit_passed", audit_passed)
        
        # Log MLflow metrics
        mlflow.log_metric("auc", metrics["auc"])
        mlflow.log_metric("ks_stat", metrics["ks"])
        mlflow.log_metric("ece", metrics["ece"])
        mlflow.log_metric("brier_score", metrics["brier_score"])
        
        # Log reliability curve plot
        mlflow.log_artifact(metrics["reliability_curve_path"])
        mlflow.log_artifact("models/fairness_report.json")
        
        # Save Model Artifact
        model_payload = {
            "base_model": base_model,
            "calibrated_model": calibrated_model,
            "feature_names": feature_cols,
            "metrics": metrics,
            "model_version": "1.0.0"
        }
        
        output_model_path = config["model"].get("output_path", "models/xgb_v1.pkl")
        os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
        joblib.dump(model_payload, output_model_path)
        print(f"Model payload successfully serialized and saved to {output_model_path}!")
        
        # Log serialized model to MLflow
        mlflow.log_artifact(output_model_path)
        
    print("\nTraining run fully completed!")

if __name__ == "__main__":
    main()
