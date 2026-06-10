import os
import pandas as pd
import pytest
from data.synthetic.generate_profiles import generate_synthetic_data, ApplicantProfile

def test_generate_profiles_schema():
    # Generate a small sample size for quick verification
    num_test = 100
    df = generate_synthetic_data(num_test, seed=42)
    
    # Assert size and structure
    assert len(df) == num_test
    assert "applicant_id" in df.columns
    assert "gender" in df.columns
    assert "geography" in df.columns
    assert "income_proxy" in df.columns
    assert "is_msme" in df.columns
    assert "default_label" in df.columns
    
    # Validate each row conforms to ApplicantProfile Pydantic schema
    for idx, row in df.iterrows():
        # Will raise ValidationError if invalid
        profile = ApplicantProfile(**row.to_dict())
        assert len(profile.upi_count) == 12
        assert len(profile.utility_status) == 12
        assert len(profile.mobile_recharge_status) == 12
        
        if profile.is_msme:
            assert len(profile.gst_status) == 12
        else:
            assert len(profile.gst_status) == 0

def test_default_rate_is_reasonable():
    # Test on a slightly larger dataset to check default rates
    df = generate_synthetic_data(1000, seed=42)
    default_rate = df["default_label"].mean()
    
    # Assert default rate is positive and within a normal range (e.g., 2% to 40%)
    assert 0.02 <= default_rate <= 0.40, f"Unexpected default rate: {default_rate}"
    
    # Verify demographics logic
    # Low income should have higher default rates than high income
    low_inc_defaults = df[df["income_proxy"] == "low"]["default_label"].mean()
    high_inc_defaults = df[df["income_proxy"] == "high"]["default_label"].mean()
    assert low_inc_defaults > high_inc_defaults
