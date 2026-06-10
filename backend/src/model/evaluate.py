import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.calibration import calibration_curve
from scipy.stats import ks_2samp

def ks_statistic(y_true, y_prob):
    """
    Computes the Kolmogorov-Smirnov statistic.
    """
    default = y_prob[y_true == 1]
    non_default = y_prob[y_true == 0]
    if len(default) == 0 or len(non_default) == 0:
        return 0.0
    return ks_2samp(default, non_default).statistic

def expected_calibration_error(y_true, y_prob, n_bins=10):
    """
    Calculates the Expected Calibration Error (ECE).
    """
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        # Avoid edge issue for 1.0 probability
        if i == n_bins - 1:
            in_bin = (y_prob >= bin_lower) & (y_prob <= bin_upper)
        else:
            in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)
            
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += prop_in_bin * np.abs(avg_confidence_in_bin - accuracy_in_bin)
    return float(ece)

def evaluate_model(y_true, y_prob, output_dir="models"):
    """
    Evaluates model performance and saves reliability curve visualization.
    """
    auc = float(roc_auc_score(y_true, y_prob))
    ks = float(ks_statistic(y_true, y_prob))
    ece = expected_calibration_error(y_true, y_prob)
    brier = float(brier_score_loss(y_true, y_prob))
    
    print("\n--- Model Evaluation Summary ---")
    print(f"AUC:        {auc:.4f}")
    print(f"KS Stat:    {ks:.4f}")
    print(f"ECE:        {ece:.4f}")
    print(f"Brier:      {brier:.4f}")
    
    # Generate and save reliability curve
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)
    
    os.makedirs(output_dir, exist_ok=True)
    plot_path = os.path.join(output_dir, "reliability_curve.png")
    
    plt.figure(figsize=(6, 6))
    plt.plot([0, 1], [0, 1], "k--", label="Perfectly Calibrated")
    plt.plot(prob_pred, prob_true, "s-", color="#0066FF", label="Calibrated Model")
    plt.xlabel("Mean Predicted Probability")
    plt.ylabel("Fraction of Defaults")
    plt.title("Reliability Curve (Calibration)")
    plt.legend(loc="lower right")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    plt.close()
    
    print(f"Reliability curve saved to {plot_path}")
    
    return {
        "auc": auc,
        "ks": ks,
        "ece": ece,
        "brier_score": brier,
        "reliability_curve_path": plot_path
    }
