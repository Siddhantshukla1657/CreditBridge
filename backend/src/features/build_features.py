import os
import yaml
import pandas as pd
from src.features import upi_features, utility_features, mobile_features, gst_features

def load_config(config_path="configs/train_config.yaml"):
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {
        "data": {
            "synthetic_output_path": "data/synthetic/profiles.parquet",
            "processed_output_path": "data/processed/features.parquet"
        }
    }

def expand_list_columns(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()
    list_cols_to_expand = [
        "upi_count", "upi_failed_count", "upi_amount", "upi_merchant_count", 
        "upi_night_count", "upi_income_deposits", "utility_status", 
        "utility_days_late", "mobile_recharge_status", "mobile_plan_value"
    ]
    for col in list_cols_to_expand:
        if col in df_out.columns:
            expanded = pd.DataFrame(df_out[col].tolist(), index=df_out.index)
            expanded.columns = [f"{col}_m{i}" for i in range(1, 13)]
            df_out = pd.concat([df_out, expanded], axis=1)
    return df_out

def main():
    config = load_config()
    input_path = config["data"]["synthetic_output_path"]
    output_path = config["data"]["processed_output_path"]
    
    print(f"Reading synthetic profiles from {input_path}...")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Synthetic data file not found at {input_path}. Please run generate_profiles.py first.")
        
    df = pd.read_parquet(input_path)
    df = expand_list_columns(df)
    
    print("Executing UPI feature transforms...")
    df = upi_features.transform(df)
    
    print("Executing Utility feature transforms...")
    df = utility_features.transform(df)
    
    print("Executing Mobile feature transforms...")
    df = mobile_features.transform(df)
    
    print("Executing GST feature transforms...")
    df = gst_features.transform(df)
    
    # Keep only the engineered features + demographics + target label
    engineered_cols = [
        "applicant_id",
        "gender",
        "geography",
        "income_proxy",
        "is_msme",
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
        "gst_penalty_count",
        "default_label"
    ]
    
    print("Filtering and saving final feature matrix...")
    final_df = df[engineered_cols]
    
    # Ensure there are no null values in the feature matrix
    null_counts = final_df.isnull().sum()
    if null_counts.sum() > 0:
        print("Warning: Null values detected in engineered feature matrix:")
        print(null_counts[null_counts > 0])
        print("Filling nulls with neutral defaults...")
        final_df = final_df.fillna(0)
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_parquet(output_path, index=False)
    print(f"Feature-engineered dataset successfully saved to {output_path} with shape {final_df.shape}!")

if __name__ == "__main__":
    main()
