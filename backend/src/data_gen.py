import pandas as pd
import numpy as np
import os

def generate_synthetic_data(num_profiles=80000):
    print(f"Generating {num_profiles} synthetic profiles...")
    np.random.seed(42)
    
    # Demographics
    applicant_ids = [f"APP_{i:06d}" for i in range(num_profiles)]
    ages = np.random.randint(18, 65, size=num_profiles)
    incomes = np.random.lognormal(mean=11.5, sigma=0.8, size=num_profiles) # roughly Rs 100k avg
    location_tier = np.random.choice([1, 2, 3], size=num_profiles, p=[0.3, 0.4, 0.3])
    
    # UPI signals
    upi_tx_count_6m = np.random.poisson(lam=150, size=num_profiles)
    upi_tx_volume_6m = upi_tx_count_6m * np.random.uniform(100, 5000, size=num_profiles)
    
    # Utility signals
    utility_on_time_6m = np.random.randint(0, 7, size=num_profiles)
    utility_delayed_6m = 6 - utility_on_time_6m
    
    # Mobile Recharge
    mobile_recharge_avg_amount_6m = np.random.uniform(150, 1000, size=num_profiles)
    mobile_recharge_days_since_last = np.random.randint(0, 45, size=num_profiles)
    
    # GST signals (only for a subset, e.g., kirana/small business owners)
    is_business = np.random.binomial(1, 0.3, size=num_profiles)
    gst_filing_regularity = is_business * np.random.uniform(0.5, 1.0, size=num_profiles)
    
    # Synthetic target based on features (higher income/on-time utilities -> lower default prob)
    # This is a basic proxy for the World Bank/Markov calibrated reality
    base_default_risk = 0.2
    income_effect = (incomes < 50000) * 0.1
    utility_effect = (utility_delayed_6m > 2) * 0.15
    upi_effect = (upi_tx_count_6m < 50) * 0.05
    
    prob_default = base_default_risk + income_effect + utility_effect + upi_effect
    prob_default = np.clip(prob_default, 0, 1)
    
    default_flag = np.random.binomial(1, prob_default)
    
    df = pd.DataFrame({
        "applicant_id": applicant_ids,
        "age": ages,
        "income": incomes,
        "location_tier": location_tier,
        "upi_tx_count_6m": upi_tx_count_6m,
        "upi_tx_volume_6m": upi_tx_volume_6m,
        "utility_on_time_6m": utility_on_time_6m,
        "utility_delayed_6m": utility_delayed_6m,
        "mobile_recharge_avg_amount_6m": mobile_recharge_avg_amount_6m,
        "mobile_recharge_days_since_last": mobile_recharge_days_since_last,
        "is_business": is_business,
        "gst_filing_regularity": gst_filing_regularity,
        "default_flag": default_flag
    })
    
    os.makedirs("data/raw", exist_ok=True)
    out_path = "data/raw/synthetic_profiles.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved generated data to {out_path}")
    
    return df

if __name__ == "__main__":
    generate_synthetic_data(80000)
