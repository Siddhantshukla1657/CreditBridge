import pandas as pd
import numpy as np
import os

def engineer_features(input_path="data/raw/synthetic_profiles.csv", output_path="data/processed/features.csv"):
    print(f"Loading raw data from {input_path}...")
    df = pd.read_csv(input_path)
    
    print("Engineering features...")
    # UPI derived features
    df['upi_avg_tx_size_6m'] = df['upi_tx_volume_6m'] / df['upi_tx_count_6m'].replace(0, 1)
    
    # Simulate 12m rolling window features based on 6m
    # In a real system, these would be aggregated from raw transaction logs
    np.random.seed(42)
    df['upi_tx_count_12m'] = df['upi_tx_count_6m'] * 2 + np.random.randint(-10, 10, size=len(df))
    df['upi_tx_count_12m'] = df['upi_tx_count_12m'].clip(lower=0)
    df['upi_tx_volume_12m'] = df['upi_tx_volume_6m'] * 2.1 + np.random.normal(0, 500, size=len(df))
    df['upi_tx_volume_12m'] = df['upi_tx_volume_12m'].clip(lower=0)
    df['upi_avg_tx_size_12m'] = df['upi_tx_volume_12m'] / df['upi_tx_count_12m'].replace(0, 1)
    
    # Velocity features
    df['upi_tx_velocity'] = df['upi_tx_count_6m'] / df['upi_tx_count_12m'].replace(0, 1)
    
    # Utility features
    df['utility_on_time_ratio_6m'] = df['utility_on_time_6m'] / 6.0
    df['utility_delayed_ratio_6m'] = df['utility_delayed_6m'] / 6.0
    
    # Simulating 12m utility
    df['utility_on_time_12m'] = df['utility_on_time_6m'] + np.random.randint(0, 7, size=len(df))
    df['utility_on_time_ratio_12m'] = df['utility_on_time_12m'] / 12.0
    
    # Financial health ratios
    # Income could be annual or monthly. Assuming monthly based on mean 11.5 lognormal (Rs 100k)
    df['income_to_upi_volume_ratio'] = df['upi_tx_volume_6m'] / df['income'].replace(0, 1)
    
    # Mobile recharge
    df['mobile_recharge_consistency'] = 1.0 / (df['mobile_recharge_days_since_last'] + 1)
    
    # GST / Business
    df['is_active_business'] = (df['is_business'] == 1) & (df['gst_filing_regularity'] >= 0.7)
    df['is_active_business'] = df['is_active_business'].astype(int)
    
    # Risk Proxy Features (Useful for models)
    df['risk_score_proxy'] = (
        (1 - df['utility_on_time_ratio_6m']) * 0.3 +
        (df['income_to_upi_volume_ratio'] > 5).astype(int) * 0.2 +
        (df['mobile_recharge_days_since_last'] > 30).astype(int) * 0.1
    )
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Engineered {len(df.columns)} features. Saved to {output_path}")
    
    return df

if __name__ == "__main__":
    engineer_features()
