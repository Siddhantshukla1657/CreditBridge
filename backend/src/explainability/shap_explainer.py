import shap
import pandas as pd
import numpy as np


class ShapExplainerWrapper:
    def __init__(self, xgb_model, feature_names):
        """
        Wrapper around shap.TreeExplainer.
        """
        self.model = xgb_model
        self.feature_names = feature_names
        # Initialize explainer on the underlying XGBoost model
        self.explainer = shap.TreeExplainer(xgb_model)

    def explain_instance(self, X_instance: pd.DataFrame):
        """
        Generates SHAP values for a single applicant instance.
        X_instance must be a pandas DataFrame of shape (1, num_features).
        """
        shap_values = self.explainer.shap_values(X_instance)

        # If shape is 2D and it's a binary classifier, check dimension
        if len(shap_values.shape) > 1 and shap_values.shape[0] == 1:
            shap_vals = shap_values[0]
        else:
            shap_vals = shap_values

        base_value = float(self.explainer.expected_value)

        # Zip features with their SHAP values
        features_shap = []
        for name, val in zip(self.feature_names, shap_vals):
            features_shap.append({
                "feature": name,
                "shap_value": float(val)
            })

        # Sort by absolute impact
        features_shap.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        # Structure waterfall data for Recharts (Top 5 + 'Other' + Final)
        top_5 = features_shap[:5]
        other_shap_sum = sum(f["shap_value"] for f in features_shap[5:])

        # Calculate start and end positions for floating bars
        waterfall_data = []
        current = base_value

        # Add base value
        waterfall_data.append({
            "name": "Base Value",
            "value": base_value,
            "start": 0.0,
            "end": base_value,
            "is_total": True
        })

        for f in top_5:
            start_pos = current
            current += f["shap_value"]
            waterfall_data.append({
                "name": f["feature"],
                "value": f["shap_value"],
                "start": start_pos,
                "end": current,
                "is_total": False
            })

        if abs(other_shap_sum) > 0.001:
            start_pos = current
            current += other_shap_sum
            waterfall_data.append({
                "name": "Other Features",
                "value": other_shap_sum,
                "start": start_pos,
                "end": current,
                "is_total": False
            })

        # Final prediction score (log-odds space)
        waterfall_data.append({
            "name": "Final Prediction",
            "value": current,
            "start": 0.0,
            "end": current,
            "is_total": True
        })

        return {
            "base_value": base_value,
            "features_shap": features_shap,
            "waterfall_data": waterfall_data
        }

    def generate_force_plot_data(self, X_instance: pd.DataFrame):
        """
        Returns structured data for a SHAP force plot.

        The force plot visualises how each feature pushes the model prediction
        away from the base value (expected model output) toward the final output.
        Positive SHAP → pushes toward higher default risk (red bar pushing right).
        Negative SHAP → pushes toward lower default risk (blue bar pushing left).

        Returns a dict compatible with the React ForcePlotChart component:
        {
            "base_value": float,          # E[f(X)] — model mean in log-odds space
            "output_value": float,        # f(x) — this applicant's log-odds output
            "features": [
                {
                    "name": str,          # feature name
                    "shap_value": float,  # contribution in log-odds
                    "feature_value": float|int|str,  # raw input value
                    "direction": "positive"|"negative"
                },
                ...
            ],
            "positive_features": [...],   # subset pushing toward higher risk
            "negative_features": [...],   # subset pushing toward lower risk
        }
        """
        shap_values = self.explainer.shap_values(X_instance)

        if len(shap_values.shape) > 1 and shap_values.shape[0] == 1:
            shap_vals = shap_values[0]
        else:
            shap_vals = shap_values

        base_value = float(self.explainer.expected_value)
        output_value = base_value + float(shap_vals.sum())

        features = []
        row = X_instance.iloc[0] if hasattr(X_instance, "iloc") else X_instance

        for name, shap_val in zip(self.feature_names, shap_vals):
            raw_val = row[name] if name in row.index else None
            # Coerce numpy scalars to plain Python types for JSON serialisation
            if hasattr(raw_val, "item"):
                raw_val = raw_val.item()

            features.append({
                "name": name,
                "shap_value": float(shap_val),
                "feature_value": raw_val,
                "direction": "positive" if shap_val > 0 else "negative",
            })

        # Sort by absolute SHAP impact (largest bars first)
        features.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        # Keep top-10 for readability; group the rest as "other"
        top_features = features[:10]
        other_sum = sum(f["shap_value"] for f in features[10:])

        if abs(other_sum) > 0.001:
            top_features.append({
                "name": "Other features",
                "shap_value": float(other_sum),
                "feature_value": None,
                "direction": "positive" if other_sum > 0 else "negative",
            })

        positive_features = [f for f in top_features if f["shap_value"] > 0]
        negative_features = [f for f in top_features if f["shap_value"] <= 0]

        return {
            "base_value": base_value,
            "output_value": output_value,
            "features": top_features,
            "positive_features": positive_features,
            "negative_features": negative_features,
        }
