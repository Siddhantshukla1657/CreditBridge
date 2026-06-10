import numpy as np

# Map of raw feature names to human-readable labels and descriptions
FEATURE_META = {
    "upi_txn_count_6m": {
        "label": "UPI Transaction Volume",
        "pos": "Frequent digital transactions show high financial engagement.",
        "neg": "Low digital transaction volume limits credit history visibility."
    },
    "upi_consistency_score": {
        "label": "UPI Cash Flow Consistency",
        "pos": "Consistent weekly UPI patterns demonstrate stable digital cash flow.",
        "neg": "Highly irregular UPI frequencies indicate unstable cash flow."
    },
    "upi_merchant_diversity": {
        "label": "Merchant Spending Diversity",
        "pos": "Transacting across varied merchant categories suggests diverse consumption.",
        "neg": "Narrow merchant payments indicate transactional concentration."
    },
    "upi_failed_rate": {
        "label": "UPI Transaction Success Rate",
        "pos": "Low transaction failure rates indicate stable balance management.",
        "neg": "High transaction failure rate suggests potential balance shortfalls."
    },
    "upi_avg_txn_value": {
        "label": "Average UPI Transaction Size",
        "pos": "Healthy average transaction size indicates strong purchasing capacity.",
        "neg": "Low average transaction sizes suggest smaller cash exchanges."
    },
    "upi_night_txn_share": {
        "label": "Night UPI Transactions Share",
        "pos": "Standard daytime transactional habits.",
        "neg": "High volume of late-night transfers may signify irregular activities."
    },
    "upi_income_regularity": {
        "label": "Income Deposit Consistency",
        "pos": "Regular monthly salary or business deposits reflect reliable income.",
        "neg": "Stochastic deposits suggest irregular or seasonal income cycles."
    },
    "utility_streak_length": {
        "label": "Utility Payment On-Time Streak",
        "pos": "Long streak of on-time utility payments showcases strong payment discipline.",
        "neg": "Short utility payment streak suggests frequent payment disruptions."
    },
    "utility_days_before_due_avg": {
        "label": "Average Utility Payment Delay",
        "pos": "Bills consistently paid well before the due date.",
        "neg": "Bills paid close to or after the due date flags potential liquidity constraints."
    },
    "utility_lapse_count_12m": {
        "label": "Utility Bill Lapses (12m)",
        "pos": "No lapsed utility bills in the past year.",
        "neg": "Lapsed utility bills indicate severe payment delay risks."
    },
    "utility_reinstatement_count": {
        "label": "Utility Reinstatement Rate",
        "pos": "Promptly restoring lapsed utility connections indicates recovery capability.",
        "neg": "Repeated connection lapses without reinstatement suggests prolonged stress."
    },
    "mobile_plan_tier": {
        "label": "Mobile Recharge Tier",
        "pos": "Premium high-value mobile plans indicate high disposable income.",
        "neg": "Low value recharges indicate limited communication spending."
    },
    "mobile_recharge_streak": {
        "label": "Mobile Recharge Consistency",
        "pos": "Timely mobile recharges show stable connectivity habits.",
        "neg": "Frequent recharge delays signal irregular wallet sizes."
    },
    "mobile_plan_trend": {
        "label": "Mobile Plan Spend Trend",
        "pos": "Upward or stable mobile spend suggests stable personal finances.",
        "neg": "Downgrading mobile recharge plans signals spending constraints."
    },
    "mobile_lapse_count": {
        "label": "Mobile Connectivity Lapses",
        "pos": "No cellular connection lapses.",
        "neg": "Frequent phone inactivity suggests temporary wallet constraints."
    },
    "gst_filing_regularity": {
        "label": "GST Filing Regularity",
        "pos": "Perfect GST compliance indicates healthy business operations.",
        "neg": "Delayed tax filings signify regulatory lapses or business stress."
    },
    "gst_turnover_trend": {
        "label": "GST Turnover Trend",
        "pos": "Growing business revenues QoQ indicates commercial success.",
        "neg": "Declining business turnover reflects commercial slowdown."
    },
    "gst_penalty_count": {
        "label": "GST Penalty Incidents",
        "pos": "No tax filing penalties incurred.",
        "neg": "Accumulated tax penalties signal regulatory and financial lapses."
    },
    "income_shock_job_loss": {
        "label": "Job Loss Incident",
        "pos": "No recent employment disruption.",
        "neg": "Recent job loss shock increases default probabilities."
    },
    "income_shock_health": {
        "label": "Health Emergency Shock",
        "pos": "No severe medical expenditure events.",
        "neg": "Recent family health emergency implies significant pocket drain."
    }
}

def generate_plain_reasons(features_shap, score_delta_scale=100.0, top_n=3):
    """
    Translates sorted SHAP values into plain-English credit explanations.
    SHAP values represent default log-odds.
    - Negative SHAP = reduces default risk = POSITIVE credit points (+pts)
    - Positive SHAP = increases default risk = NEGATIVE credit points (-pts)
    """
    reasons = []
    
    # Process the top N features
    for item in features_shap[:top_n]:
        feature_name = item["feature"]
        shap_val = item["shap_value"]
        
        # Determine the base feature name if encoded
        base_name = feature_name
        for prefix in ["geography_", "gender_", "income_"]:
            if feature_name.startswith(prefix):
                base_name = feature_name  # Keep the encoded key if matching
                
        # Fallback to feature_name if not in META dictionary
        meta = FEATURE_META.get(base_name, {
            "label": feature_name.replace("_", " ").title(),
            "pos": "Positive signal detected.",
            "neg": "Adjustment to credit capacity."
        })
        
        # Calculate impact points
        # If SHAP is negative, default risk drops -> credit score rises (+ points)
        points = int(np.round(-shap_val * score_delta_scale))
        
        if points == 0:
            continue
            
        direction = "+" if points > 0 else ""
        description = meta["pos"] if points > 0 else meta["neg"]
        
        reasons.append({
            "feature": feature_name,
            "label": meta["label"],
            "points": points,
            "text": f"{meta['label']} ({direction}{points} pts): {description}"
        })
        
    return reasons
