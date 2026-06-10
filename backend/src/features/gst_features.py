import pandas as pd
import numpy as np

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes 3 GST features:
    - gst_filing_regularity: count of 'filed' months in the last 12m (imputed as 12 for non-MSMEs)
    - gst_turnover_trend: QoQ turnover ratio (m10-m12) / (m7-m9) (imputed as 1.0 for non-MSMEs)
    - gst_penalty_count: sum of penalty values in 12m (imputed as 0.0 for non-MSMEs)
    """
    out_df = df.copy()
    
    # Initialize default values for non-MSMEs
    out_df["gst_filing_regularity"] = 12
    out_df["gst_turnover_trend"] = 1.0
    out_df["gst_penalty_count"] = 0.0
    
    # Filter MSMEs index
    msme_mask = out_df["is_msme"] == True
    
    if msme_mask.any():
        months_12m = [f"m{i}" for i in range(1, 13)]
        months_q4 = [f"m{i}" for i in range(10, 13)]
        months_q3 = [f"m{i}" for i in range(7, 10)]
        
        # Calculate status list counts row-wise for MSMEs
        # Note: raw columns are stored as lists in profiles parquet, or we can index them.
        # But wait! In generate_profiles.py, they are dumped as lists under: gst_status, gst_turnover, gst_penalties.
        # So in pandas, row['gst_status'] is a Python list! Let's process them accordingly.
        
        def compute_msme_gst_features(row):
            status_list = row["gst_status"]
            turnover_list = row["gst_turnover"]
            penalty_list = row["gst_penalties"]
            
            # 1. filing regularity: count of 'filed' in last 12
            reg = sum(1 for s in status_list if s == "filed")
            
            # 2. turnover trend: QoQ (m10-12) / (m7-9)
            # note that in python lists: m1 is list[0], m12 is list[11]
            q4_avg = np.mean(turnover_list[9:12]) if len(turnover_list) >= 12 else 0.0
            q3_avg = np.mean(turnover_list[6:9]) if len(turnover_list) >= 9 else 0.0
            trend = q4_avg / q3_avg if q3_avg > 0.0 else 1.0
            
            # 3. penalty count: sum of penalties
            penalties = sum(penalty_list)
            
            return pd.Series([reg, trend, penalties])
            
        msme_features = out_df[msme_mask].apply(compute_msme_gst_features, axis=1)
        out_df.loc[msme_mask, "gst_filing_regularity"] = msme_features[0].astype(int)
        out_df.loc[msme_mask, "gst_turnover_trend"] = msme_features[1].astype(float)
        out_df.loc[msme_mask, "gst_penalty_count"] = msme_features[2].astype(float)
        
    cols_to_keep = ["applicant_id", "gst_filing_regularity", "gst_turnover_trend", "gst_penalty_count"]
    
    df_dropped = df.drop(columns=[c for c in cols_to_keep if c != "applicant_id" and c in df.columns])
    return pd.merge(df_dropped, out_df[cols_to_keep], on="applicant_id", how="left")
