import numpy as np

def probability_to_score(prob_default: float) -> int:
    """
    Maps default probability to a 300-900 score.
    Higher score means lower default probability.
    """
    # 0.0 prob -> 900, 1.0 prob -> 300
    score = 900.0 - 600.0 * prob_default
    # Clamp to [300, 900]
    score = max(300, min(900, score))
    return int(np.round(score))

def score_to_band(score: int) -> str:
    """
    Maps score value to a qualitative CreditBand.
    - Prime (750–900)
    - Near-prime (650–749)
    - Subprime (550–649)
    - High risk (400–549)
    - Decline (300–399)
    """
    if score >= 750:
        return "Prime"
    elif score >= 650:
        return "Near-prime"
    elif score >= 550:
        return "Subprime"
    elif score >= 400:
        return "High risk"
    else:
        return "Decline"

def predict_score_details(model, X_preprocessed):
    """
    Runs model inference, grabs probabilities, scores, and bands.
    X_preprocessed should be a 2D numpy array or pandas DataFrame.
    """
    # Predict default probabilities (Platt-calibrated outputs)
    probs = model.predict_proba(X_preprocessed)[:, 1]
    
    scores = [probability_to_score(p) for p in probs]
    bands = [score_to_band(s) for s in scores]
    
    # Calculate confidence: model confidence in predictions
    # E.g. distance from boundary (0.5), mapped to [0, 1]
    # confidence = 2 * |prob - 0.5|
    confidences = [float(np.round(2.0 * np.abs(p - 0.5), 4)) for p in probs]
    
    return {
        "probabilities": probs.tolist(),
        "scores": scores,
        "bands": bands,
        "confidences": confidences
    }
