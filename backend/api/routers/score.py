from fastapi import APIRouter, Request, HTTPException, status
import uuid
import json
import sqlite3
import pandas as pd
import numpy as np

from api.schemas import ApplicantInput, ScoreResponse, FactorItem, WaterfallItem, ForcePlotData, ForceFeatureItem
from src.features import upi_features, utility_features, mobile_features, gst_features
from src.model.train import preprocess_features
from src.model.predict import probability_to_score, score_to_band, predict_score_details
from src.explainability.shap_explainer import ShapExplainerWrapper
from src.explainability.reason_generator import generate_plain_reasons

router = APIRouter()

def get_db_connection(db_url: str):
    db_path = db_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@router.post("/score", response_model=ScoreResponse)
async def score_applicant(applicant: ApplicantInput, request: Request):
    db_url = request.app.state.db_url
    model_payload = request.app.state.model_payload
    fairness_report = request.app.state.fairness_report
    
    if not model_payload:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded. Please train the model first."
        )
        
    calibrated_model = model_payload["calibrated_model"]
    base_model = model_payload["base_model"]
    feature_names = model_payload["feature_names"]
    model_version = model_payload.get("model_version", "1.0.0")
    
    app_id = applicant.applicant_id or f"IND-API-{uuid.uuid4().hex[:8].upper()}"
    
    # 1. Check database cache
    conn = get_db_connection(db_url)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM score_cache WHERE id = ?", (app_id,))
    cached = cursor.fetchone()
    
    if cached:
        conn.close()
        raw_fpd = cached["force_plot_data"]
        force_plot_obj = None
        if raw_fpd:
            import json as _json
            fpd = _json.loads(raw_fpd)
            force_plot_obj = ForcePlotData(
                base_value=fpd["base_value"],
                output_value=fpd["output_value"],
                features=[ForceFeatureItem(**f) for f in fpd["features"]],
                positive_features=[ForceFeatureItem(**f) for f in fpd["positive_features"]],
                negative_features=[ForceFeatureItem(**f) for f in fpd["negative_features"]],
            )
        return ScoreResponse(
            applicant_id=cached["id"],
            score=cached["score"],
            band=cached["band"],
            default_probability=cached["default_prob"],
            confidence=cached["confidence"],
            top_factors=json.loads(cached["top_factors"]),
            waterfall_data=json.loads(cached["waterfall_data"]),
            force_plot_data=force_plot_obj,
            fairness_flags=json.loads(cached["fairness_flags"]),
            model_version=cached["model_version"]
        )
        
    # 2. Convert raw request inputs to a Pandas DataFrame row
    raw_dict = applicant.model_dump()
    raw_dict["applicant_id"] = app_id
    
    # Convert list inputs to pandas-friendly structures
    # The transform functions expect raw columns as lists or individual columns if split.
    # In generate_profiles, list columns like upi_count were generated, and our features modules
    # read them directly. So we keep them as list cells inside the DataFrame row!
    df_row = pd.DataFrame([raw_dict])
    from src.features.build_features import expand_list_columns
    df_row = expand_list_columns(df_row)
    
    # 3. Apply Feature Engineering Transforms
    try:
        df_row = upi_features.transform(df_row)
        df_row = utility_features.transform(df_row)
        df_row = mobile_features.transform(df_row)
        df_row = gst_features.transform(df_row)
    except Exception as e:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error in feature engineering: {str(e)}"
        )
        
    # 4. Preprocess Categorical Attributes
    df_prep = preprocess_features(df_row)
    X_instance = df_prep[feature_names]
    
    # 5. Model Inference (Probabilities & Scores)
    pred_details = predict_score_details(calibrated_model, X_instance)
    prob_default = float(pred_details["probabilities"][0])
    score = int(pred_details["scores"][0])
    band = str(pred_details["bands"][0])
    confidence = float(pred_details["confidences"][0])
    
    # 6. SHAP Explanations
    shap_wrapper = ShapExplainerWrapper(base_model, feature_names)
    explanation = shap_wrapper.explain_instance(X_instance)
    
    # 7. Generate Plain Reasons
    reasons = generate_plain_reasons(explanation["features_shap"], top_n=3)
    
    top_factors = [
        FactorItem(
            feature=r["feature"],
            label=r["label"],
            points=r["points"],
            text=r["text"]
        ) for r in reasons
    ]
    
    waterfall_data = [
        WaterfallItem(
            name=w["name"],
            value=w["value"],
            start=w["start"],
            end=w["end"],
            is_total=w["is_total"]
        ) for w in explanation["waterfall_data"]
    ]

    # 8. SHAP Force Plot
    raw_force = shap_wrapper.generate_force_plot_data(X_instance)
    force_plot_data = ForcePlotData(
        base_value=raw_force["base_value"],
        output_value=raw_force["output_value"],
        features=[ForceFeatureItem(**f) for f in raw_force["features"]],
        positive_features=[ForceFeatureItem(**f) for f in raw_force["positive_features"]],
        negative_features=[ForceFeatureItem(**f) for f in raw_force["negative_features"]],
    )
    
    # 9. Fairness Flags
    fairness_flags = []
    if fairness_report and not fairness_report.get("passed", True):
        for violation in fairness_report.get("violations", []):
            # Check if this applicant falls into the violating demographic group
            attr = violation["attribute"] # e.g. "low"
            group = violation["group"] # e.g. "income_proxy"
            
            # Read input value
            user_val = getattr(applicant, group, None)
            if user_val == attr:
                fairness_flags.append(
                    f"Model-level {violation['metric']} disparity warning for {group}='{attr}'."
                )
                
    # 10. Insert into database cache
    try:
        cursor.execute(
            """
            INSERT INTO score_cache (id, score, band, default_prob, confidence, top_factors, waterfall_data, force_plot_data, fairness_flags, model_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                app_id,
                score,
                band,
                prob_default,
                confidence,
                json.dumps([f.model_dump() for f in top_factors]),
                json.dumps([w.model_dump() for w in waterfall_data]),
                json.dumps(raw_force),
                json.dumps(fairness_flags),
                model_version
            )
        )
        conn.commit()
    except Exception as e:
        print(f"Error caching score to DB: {e}")
    finally:
        conn.close()
        
    return ScoreResponse(
        applicant_id=app_id,
        score=score,
        band=band,
        default_probability=prob_default,
        confidence=confidence,
        top_factors=top_factors,
        waterfall_data=waterfall_data,
        force_plot_data=force_plot_data,
        fairness_flags=fairness_flags,
        model_version=model_version
    )

@router.get("/score/{applicant_id}", response_model=ScoreResponse)
async def get_score(applicant_id: str, request: Request):
    db_url = request.app.state.db_url
    
    conn = get_db_connection(db_url)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM score_cache WHERE id = ?", (applicant_id,))
    cached = cursor.fetchone()
    conn.close()
    
    if not cached:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score not found for applicant {applicant_id}."
        )
        
    return ScoreResponse(
        applicant_id=cached["id"],
        score=cached["score"],
        band=cached["band"],
        default_probability=cached["default_prob"],
        confidence=cached["confidence"],
        top_factors=json.loads(cached["top_factors"]),
        waterfall_data=json.loads(cached["waterfall_data"]),
        fairness_flags=json.loads(cached["fairness_flags"]),
        model_version=cached["model_version"]
    )

@router.get("/model-card")
async def get_model_card(request: Request):
    model_payload = request.app.state.model_payload
    fairness_report = request.app.state.fairness_report
    
    if not model_payload:
        return {
            "status": "No model loaded",
            "model_version": "None"
        }
        
    metrics = model_payload.get("metrics", {})
    return {
        "model_name": "CreditBridge alternative credit scoring model",
        "model_version": model_payload.get("model_version", "1.0.0"),
        "framework": "XGBoost + Platt Calibration",
        "performance_metrics": {
            "AUC": metrics.get("auc"),
            "KS_Statistic": metrics.get("ks"),
            "Expected_Calibration_Error_ECE": metrics.get("ece"),
            "Brier_Score": metrics.get("brier_score")
        },
        "fairness_audit": fairness_report or {"status": "No audit data"}
    }
