import pandas as pd
import numpy as np

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes 4 utility features:
    - utility_streak_length: longest consecutive sequence of 'on_time' payments (12m)
    - utility_days_before_due_avg: average days late (6m: m7 to m12)
    - utility_lapse_count_12m: count of 'lapsed' payments (12m)
    - utility_reinstatement_count: count of transitions from 'lapsed' to 'on_time'/'late' (12m)
    """
    out_df = df.copy()
    
    months_12m = [f"m{i}" for i in range(1, 13)]
    months_6m = [f"m{i}" for i in range(7, 13)]
    
    # 1. utility_streak_length
    def get_streak(row):
        max_streak = 0
        curr_streak = 0
        for m in months_12m:
            if row[f"utility_status_{m}"] == "on_time":
                curr_streak += 1
                max_streak = max(max_streak, curr_streak)
            else:
                curr_streak = 0
        return max_streak
        
    out_df["utility_streak_length"] = df.apply(get_streak, axis=1)
    
    # 2. utility_days_before_due_avg
    days_late_6m_cols = [f"utility_days_late_{m}" for m in months_6m]
    out_df["utility_days_before_due_avg"] = df[days_late_6m_cols].mean(axis=1)
    
    # 3. utility_lapse_count_12m
    status_12m_cols = [f"utility_status_{m}" for m in months_12m]
    out_df["utility_lapse_count_12m"] = (df[status_12m_cols] == "lapsed").sum(axis=1)
    
    # 4. utility_reinstatement_count
    def get_reinstatements(row):
        count = 0
        for i in range(1, 12):
            prev = row[f"utility_status_m{i}"]
            curr = row[f"utility_status_m{i+1}"]
            if prev == "lapsed" and curr in ["on_time", "late"]:
                count += 1
        return count
        
    out_df["utility_reinstatement_count"] = df.apply(get_reinstatements, axis=1)
    
    cols_to_keep = ["applicant_id", "utility_streak_length", "utility_days_before_due_avg", 
                    "utility_lapse_count_12m", "utility_reinstatement_count"]
    
    df_dropped = df.drop(columns=[c for c in cols_to_keep if c != "applicant_id" and c in df.columns])
    return pd.merge(df_dropped, out_df[cols_to_keep], on="applicant_id", how="left")
