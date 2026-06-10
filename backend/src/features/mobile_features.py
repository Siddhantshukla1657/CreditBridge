import pandas as pd
import numpy as np

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes 4 mobile features:
    - mobile_plan_tier: tier category (1=low, 2=mid, 3=high) based on m12 recharge value
    - mobile_recharge_streak: longest consecutive sequence of 'on_time' (12m)
    - mobile_plan_trend: ratio of average value (m7-m12) / average value (m1-m6)
    - mobile_lapse_count: count of 'lapsed' months (12m)
    """
    out_df = df.copy()
    
    months_12m = [f"m{i}" for i in range(1, 13)]
    months_6m_prior = [f"m{i}" for i in range(1, 7)]
    months_6m_recent = [f"m{i}" for i in range(7, 13)]
    
    # 1. mobile_plan_tier
    val_m12 = df["mobile_plan_value_m12"]
    out_df["mobile_plan_tier"] = np.where(val_m12 <= 200.0, 1, np.where(val_m12 <= 500.0, 2, 3))
    
    # 2. mobile_recharge_streak
    def get_streak(row):
        max_streak = 0
        curr_streak = 0
        for m in months_12m:
            if row[f"mobile_recharge_status_{m}"] == "on_time":
                curr_streak += 1
                max_streak = max(max_streak, curr_streak)
            else:
                curr_streak = 0
        return max_streak
        
    out_df["mobile_recharge_streak"] = df.apply(get_streak, axis=1)
    
    # 3. mobile_plan_trend
    avg_recent = df[[f"mobile_plan_value_{m}" for m in months_6m_recent]].mean(axis=1)
    avg_prior = df[[f"mobile_plan_value_{m}" for m in months_6m_prior]].mean(axis=1)
    out_df["mobile_plan_trend"] = np.where(avg_prior > 0.0, avg_recent / avg_prior, 1.0)
    
    # 4. mobile_lapse_count
    status_cols = [f"mobile_recharge_status_{m}" for m in months_12m]
    out_df["mobile_lapse_count"] = (df[status_cols] == "lapsed").sum(axis=1)
    
    cols_to_keep = ["applicant_id", "mobile_plan_tier", "mobile_recharge_streak", 
                    "mobile_plan_trend", "mobile_lapse_count"]
    
    df_dropped = df.drop(columns=[c for c in cols_to_keep if c != "applicant_id" and c in df.columns])
    return pd.merge(df_dropped, out_df[cols_to_keep], on="applicant_id", how="left")
