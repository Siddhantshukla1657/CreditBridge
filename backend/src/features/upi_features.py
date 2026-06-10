import pandas as pd
import numpy as np

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes 7 UPI features over a rolling 6-month window (m7 to m12).
    """
    out_df = df.copy()
    
    # Identify the last 6 months columns (m7 to m12)
    months_6m = [f"m{i}" for i in range(7, 13)]
    
    upi_count_cols = [f"upi_count_{m}" for m in months_6m]
    upi_failed_cols = [f"upi_failed_count_{m}" for m in months_6m]
    upi_amount_cols = [f"upi_amount_{m}" for m in months_6m]
    upi_merchant_cols = [f"upi_merchant_count_{m}" for m in months_6m]
    upi_night_cols = [f"upi_night_count_{m}" for m in months_6m]
    upi_deposit_cols = [f"upi_income_deposits_{m}" for m in months_6m]
    
    # 1. upi_txn_count_6m
    out_df["upi_txn_count_6m"] = df[upi_count_cols].sum(axis=1)
    
    # 2. upi_consistency_score: 1 / (1 + std_dev_of_monthly_counts)
    monthly_std = df[upi_count_cols].std(axis=1)
    out_df["upi_consistency_score"] = 1.0 / (1.0 + monthly_std)
    
    # 3. upi_merchant_diversity: sum(merchants) / sum(counts)
    total_txns = out_df["upi_txn_count_6m"]
    total_merchants = df[upi_merchant_cols].sum(axis=1)
    out_df["upi_merchant_diversity"] = np.where(total_txns > 0, total_merchants / total_txns, 0.0)
    
    # 4. upi_failed_rate: sum(failed) / sum(counts)
    total_failed = df[upi_failed_cols].sum(axis=1)
    out_df["upi_failed_rate"] = np.where(total_txns > 0, total_failed / total_txns, 0.0)
    
    # 5. upi_avg_txn_value: sum(amount) / sum(counts)
    total_amount = df[upi_amount_cols].sum(axis=1)
    out_df["upi_avg_txn_value"] = np.where(total_txns > 0, total_amount / total_txns, 0.0)
    
    # 6. upi_night_txn_share: sum(night_counts) / sum(counts)
    total_night = df[upi_night_cols].sum(axis=1)
    out_df["upi_night_txn_share"] = np.where(total_txns > 0, total_night / total_txns, 0.0)
    
    # 7. upi_income_regularity: fraction of last 6 months with >= 1 deposit
    deposit_months = (df[upi_deposit_cols] >= 1).sum(axis=1)
    out_df["upi_income_regularity"] = deposit_months / 6.0
    
    # Keep only the engineered features and base details
    cols_to_keep = ["applicant_id", "upi_txn_count_6m", "upi_consistency_score", 
                    "upi_merchant_diversity", "upi_failed_rate", "upi_avg_txn_value", 
                    "upi_night_txn_share", "upi_income_regularity"]
    
    # Merge engineered features back to original df while avoiding duplicate columns
    # We drop the newly created ones from the original first, then merge
    df_dropped = df.drop(columns=[c for c in cols_to_keep if c != "applicant_id" and c in df.columns])
    return pd.merge(df_dropped, out_df[cols_to_keep], on="applicant_id", how="left")
