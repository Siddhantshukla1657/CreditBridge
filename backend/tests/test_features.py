import pandas as pd
import pytest
from src.features import upi_features, utility_features, mobile_features, gst_features

@pytest.fixture
def sample_raw_data():
    # Create a dummy DataFrame replicating the synthetic profile schema
    data = {
        "applicant_id": ["IND-001", "IND-002"],
        "gender": ["M", "F"],
        "geography": ["urban", "rural"],
        "income_proxy": ["high", "low"],
        "is_msme": [True, False],
        "default_label": [0, 1]
    }
    
    # Add monthly UPI count (m1 to m12)
    for m in range(1, 13):
        data[f"upi_count_m{m}"] = [20, 5]
        data[f"upi_failed_count_m{m}"] = [1, 0]
        data[f"upi_amount_m{m}"] = [5000.0, 500.0]
        data[f"upi_merchant_count_m{m}"] = [10, 2]
        data[f"upi_night_count_m{m}"] = [2, 0]
        data[f"upi_income_deposits_m{m}"] = [1, 0]
        
        data[f"utility_status_m{m}"] = ["on_time", "lapsed"]
        data[f"utility_days_late_m{m}"] = [-5.0, 45.0]
        
        data[f"mobile_recharge_status_m{m}"] = ["on_time", "late"]
        data[f"mobile_plan_value_m{m}"] = [599.0, 179.0]
        
    # GST data for IND-001, empty/None list or empty list for IND-002
    data["gst_status"] = [["filed"] * 12, []]
    data["gst_turnover"] = [[100000.0] * 12, []]
    data["gst_penalties"] = [[0.0] * 12, []]
    
    return pd.DataFrame(data)

def test_upi_features(sample_raw_data):
    df_out = upi_features.transform(sample_raw_data)
    assert "upi_txn_count_6m" in df_out.columns
    assert "upi_consistency_score" in df_out.columns
    assert "upi_failed_rate" in df_out.columns
    assert df_out["upi_txn_count_6m"].iloc[0] == 120
    assert df_out["upi_failed_rate"].iloc[0] == 6/120

def test_utility_features(sample_raw_data):
    df_out = utility_features.transform(sample_raw_data)
    assert "utility_streak_length" in df_out.columns
    assert "utility_days_before_due_avg" in df_out.columns
    assert "utility_lapse_count_12m" in df_out.columns
    
    # IND-001 has 12 consecutive 'on_time' payments -> streak = 12
    assert df_out["utility_streak_length"].iloc[0] == 12
    # IND-002 has 12 'lapsed' payments -> streak = 0, lapse_count = 12
    assert df_out["utility_streak_length"].iloc[1] == 0
    assert df_out["utility_lapse_count_12m"].iloc[1] == 12

def test_mobile_features(sample_raw_data):
    df_out = mobile_features.transform(sample_raw_data)
    assert "mobile_plan_tier" in df_out.columns
    assert "mobile_recharge_streak" in df_out.columns
    assert "mobile_plan_trend" in df_out.columns
    
    # IND-001 has 599 recharge value -> tier 3
    assert df_out["mobile_plan_tier"].iloc[0] == 3
    # IND-002 has 179 recharge value -> tier 1
    assert df_out["mobile_plan_tier"].iloc[1] == 1

def test_gst_features(sample_raw_data):
    df_out = gst_features.transform(sample_raw_data)
    assert "gst_filing_regularity" in df_out.columns
    assert "gst_turnover_trend" in df_out.columns
    assert "gst_penalty_count" in df_out.columns
    
    # IND-001 is MSME -> filed 12/12
    assert df_out["gst_filing_regularity"].iloc[0] == 12
    # IND-002 is not MSME -> imputed 12
    assert df_out["gst_filing_regularity"].iloc[1] == 12
    assert df_out["gst_penalty_count"].iloc[1] == 0.0
