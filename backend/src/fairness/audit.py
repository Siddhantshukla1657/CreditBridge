import pandas as pd
import numpy as np
import json
import os
from aequitas.group import Group
from aequitas.bias import Bias

class FairnessViolationError(Exception):
    """
    Raised when a model fails to meet the defined fairness disparity thresholds.
    """
    pass

def run_fairness_audit(df_original: pd.DataFrame, y_true: np.ndarray, y_pred_default: np.ndarray, config: dict, output_path="models/fairness_report.json"):
    """
    Runs an Aequitas fairness audit on model predictions.
    y_pred_default: binary default prediction (1 = default, 0 = no default)
    y_true: binary default ground truth (1 = default, 0 = no default)
    """
    print("\n--- Running Aequitas Fairness Audit ---")
    
    # We define:
    # score = 1 if approved (no default prediction), 0 if denied (default prediction)
    # label_value = 1 if actually solvent (no default), 0 if defaulted
    score_approval = (y_pred_default == 0).astype(int)
    label_solvent = (y_true == 0).astype(int)
    
    protected_cols = config["fairness"]["protected_attributes"]
    ref_groups = config["fairness"]["reference_groups"]
    threshold = config["fairness"]["disparity_threshold"]
    
    # Construct Aequitas audit DataFrame
    audit_data = pd.DataFrame({
        "score": score_approval,
        "label_value": label_solvent
    })
    for col in protected_cols:
        audit_data[col] = df_original[col].values
        
    # Group analysis
    g = Group()
    xtab, _ = g.get_crosstabs(audit_data)
    
    # Bias analysis
    b = Bias()
    bdf = b.get_disparity_predefined_groups(xtab, audit_data, ref_groups)
    
    # Analyze disparities
    violations = []
    summary_report = {}
    
    # Disparities columns in Aequitas:
    # Selection Rate Disparity (Demographic Parity): 'selection_rate_disparity'
    # True Positive Rate Disparity (Equal Opportunity): 'tpr_disparity'
    # False Positive Rate Disparity: 'fpr_disparity'
    
    metrics_to_check = {
        "selection_rate_disparity": "Demographic Parity",
        "tpr_disparity": "Equal Opportunity",
        "fpr_disparity": "FPR Parity"
    }
    
    for idx, row in bdf.iterrows():
        attribute = row["attribute_value"]
        group = row["attribute_name"]
        
        # Check each metric
        for metric, label in metrics_to_check.items():
            if metric in row and not pd.isna(row[metric]):
                val = float(row[metric])
                
                # Aequitas computes disparity relative to reference group (ref value is 1.0)
                # Disparity should be within [1 - threshold, 1 + threshold] (e.g. 0.90 to 1.10)
                lower_bound = 1.0 - threshold
                upper_bound = 1.0 + threshold
                
                if val < lower_bound or val > upper_bound:
                    violations.append({
                        "attribute": attribute,
                        "group": group,
                        "metric": label,
                        "value": val,
                        "status": "FAIL"
                    })
                    
        # Add to summary
        if group not in summary_report:
            summary_report[group] = {}
        summary_report[group][attribute] = {
            "demographic_parity_disparity": float(row.get("selection_rate_disparity", 1.0)),
            "equal_opportunity_disparity": float(row.get("tpr_disparity", 1.0)),
            "fpr_parity_disparity": float(row.get("fpr_disparity", 1.0))
        }
        
    print(f"Fairness Audit complete. Checked attributes: {protected_cols}")
    print(f"Violations detected: {len(violations)}")
    for v in violations:
        print(f"  - {v['metric']} violation for {v['group']}='{v['attribute']}': value={v['value']:.3f}")
        
    # Write report
    report_data = {
        "disparity_threshold": threshold,
        "violations": violations,
        "groups": summary_report,
        "passed": len(violations) == 0
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report_data, f, indent=4)
        
    if len(violations) > 0:
        raise FairnessViolationError(f"Model failed fairness audit with {len(violations)} violations. Report saved to {output_path}")
        
    print("Fairness audit passed! Report saved to", output_path)
    return report_data
