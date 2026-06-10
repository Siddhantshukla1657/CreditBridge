import os
import yaml
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from typing import List
import argparse

# Load config
def load_config(config_path="configs/train_config.yaml"):
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {
        "data": {
            "num_profiles": 80000,
            "random_seed": 42,
            "synthetic_output_path": "data/synthetic/profiles.parquet"
        }
    }

# Pydantic v2 validation schema for single applicant profiles
class ApplicantProfile(BaseModel):
    applicant_id: str
    gender: str = Field(pattern="^(M|F)$")
    geography: str = Field(pattern="^(urban|semi-urban|rural)$")
    income_proxy: str = Field(pattern="^(high|mid|low)$")
    is_msme: bool
    
    # UPI signals
    upi_count: List[int]
    upi_failed_count: List[int]
    upi_amount: List[float]
    upi_merchant_count: List[int]
    upi_night_count: List[int]
    upi_income_deposits: List[int]
    
    # Utility signals
    utility_status: List[str]
    utility_days_late: List[float]
    
    # Mobile signals
    mobile_recharge_status: List[str]
    mobile_plan_value: List[float]
    
    # GST signals (empty if not MSME)
    gst_status: List[str]
    gst_turnover: List[float]
    gst_penalties: List[float]
    
    # Shocks
    income_shock_job_loss: bool
    income_shock_health: bool
    
    # Target
    default_label: int = Field(ge=0, le=1)

def generate_synthetic_data(num_profiles: int, seed: int):
    np.random.seed(seed)
    
    profiles = []
    
    # World Bank Findex calibrated distributions for India
    genders = np.random.choice(["M", "F"], size=num_profiles, p=[0.52, 0.48])
    geographies = np.random.choice(["urban", "semi-urban", "rural"], size=num_profiles, p=[0.30, 0.35, 0.35])
    income_proxies = np.random.choice(["high", "mid", "low"], size=num_profiles, p=[0.20, 0.50, 0.30])
    is_msmes = np.random.choice([True, False], size=num_profiles, p=[0.20, 0.80])
    
    # Markov chain transition matrices for Utility and Mobile billing streaks
    # State mapping: 0=on_time, 1=late, 2=lapsed
    states = ["on_time", "late", "lapsed"]
    
    # Transition probabilities for creditworthy (low default risk) profiles
    p_good = np.array([
        [0.90, 0.08, 0.02],  # from on_time
        [0.60, 0.30, 0.10],  # from late
        [0.30, 0.30, 0.40]   # from lapsed
    ])
    
    # Transition probabilities for high-risk profiles
    p_bad = np.array([
        [0.60, 0.30, 0.10],  # from on_time
        [0.40, 0.40, 0.20],  # from late
        [0.15, 0.25, 0.60]   # from lapsed
    ])

    for i in range(num_profiles):
        app_id = f"IND-2026-{i:06d}"
        gender = genders[i]
        geo = geographies[i]
        inc = income_proxies[i]
        msme = bool(is_msmes[i])
        
        # Decide if this profile is inherently high-risk (unobserved trait)
        is_risky = False
        if inc == "low":
            is_risky = np.random.rand() < 0.45
        elif inc == "mid":
            is_risky = np.random.rand() < 0.20
        else:
            is_risky = np.random.rand() < 0.05
            
        # Shocks
        shock_job = np.random.rand() < 0.08
        shock_health = np.random.rand() < 0.05
        
        if shock_job or shock_health:
            is_risky = np.random.rand() < 0.75 or is_risky
            
        trans_matrix = p_bad if is_risky else p_good
        
        # --- Generate UPI ---
        # Beta distribution base probability for UPI usage
        # Calibrate lambda base on income proxy
        inc_multiplier = {"high": 1.8, "mid": 1.0, "low": 0.5}[inc]
        upi_base_txns = np.random.beta(a=3, b=2) * 40 * inc_multiplier
        
        upi_count = []
        upi_failed_count = []
        upi_amount = []
        upi_merchant_count = []
        upi_night_count = []
        upi_income_deposits = []
        
        for m in range(12):
            # UPI monthly transactions
            lambda_txns = max(2, upi_base_txns * np.random.uniform(0.8, 1.2))
            cnt = int(np.random.poisson(lambda_txns))
            upi_count.append(cnt)
            
            # Failed txns rate: higher for risky profiles or connection dropouts
            fail_p = 0.12 if is_risky else 0.04
            fail_p += np.random.uniform(0.0, 0.05)
            failed = int(np.random.binomial(cnt, min(0.9, fail_p))) if cnt > 0 else 0
            upi_failed_count.append(failed)
            
            # Average txn value: higher for high income
            avg_val = {"high": 1200.0, "mid": 450.0, "low": 150.0}[inc]
            avg_val *= np.random.uniform(0.7, 1.3)
            upi_amount.append(float(np.round(cnt * avg_val, 2)))
            
            # Merchant diversity: distinct merchants
            merch = int(min(cnt, np.random.poisson(cnt * 0.6))) if cnt > 0 else 0
            upi_merchant_count.append(merch)
            
            # Night transactions (10pm-6am)
            night = int(np.random.binomial(cnt, 0.15)) if cnt > 0 else 0
            upi_night_count.append(night)
            
            # Income deposits (salary/gains): high/mid have standard salary deposits
            if inc == "high":
                dep = int(np.random.choice([1, 2], p=[0.9, 0.1]))
            elif inc == "mid":
                dep = int(np.random.choice([0, 1, 2], p=[0.1, 0.8, 0.1]))
            else:
                dep = int(np.random.choice([0, 1], p=[0.6, 0.4]))
            upi_income_deposits.append(dep)
            
        # --- Generate Utility ---
        util_status = []
        util_days_late = []
        curr_state = np.random.choice([0, 1, 2], p=[0.8, 0.15, 0.05])
        
        for m in range(12):
            curr_state = np.random.choice([0, 1, 2], p=trans_matrix[curr_state])
            status = states[curr_state]
            util_status.append(status)
            
            if status == "on_time":
                days = float(np.random.uniform(-10, 0))
            elif status == "late":
                days = float(np.random.uniform(1, 30))
            else:
                days = float(np.random.uniform(31, 90))
            util_days_late.append(float(np.round(days, 2)))
            
        # --- Generate Mobile ---
        mob_status = []
        mob_plan = []
        curr_state_mob = np.random.choice([0, 1, 2], p=[0.85, 0.10, 0.05])
        plan_base = {"high": 799.0, "mid": 299.0, "low": 179.0}[inc]
        
        for m in range(12):
            curr_state_mob = np.random.choice([0, 1, 2], p=trans_matrix[curr_state_mob])
            status = states[curr_state_mob]
            mob_status.append(status)
            
            if status == "lapsed":
                val = 0.0
            else:
                # Add slight random trend
                val = plan_base * np.random.choice([0.8, 1.0, 1.2], p=[0.1, 0.8, 0.1])
            mob_plan.append(float(np.round(val, 2)))
            
        # --- Generate GST (if MSME) ---
        gst_stat = []
        gst_turn = []
        gst_pen = []
        
        if msme:
            curr_state_gst = np.random.choice([0, 1, 2], p=[0.90, 0.08, 0.02])
            turn_base = {"high": 350000.0, "mid": 120000.0, "low": 45000.0}[inc]
            
            for m in range(12):
                curr_state_gst = np.random.choice([0, 1, 2], p=trans_matrix[curr_state_gst])
                # map state index to: filed (on_time), late (late), unfiled (lapsed)
                status = "filed" if curr_state_gst == 0 else ("late" if curr_state_gst == 1 else "unfiled")
                gst_stat.append(status)
                
                turnover = turn_base * np.random.uniform(0.7, 1.3)
                if status == "unfiled":
                    turnover = 0.0
                gst_turn.append(float(np.round(turnover, 2)))
                
                penalty = 0.0
                if status == "late":
                    penalty = float(np.random.choice([100.0, 200.0, 500.0]))
                elif status == "unfiled":
                    penalty = 1000.0
                gst_pen.append(penalty)
        else:
            # Empty lists if not MSME
            gst_stat = []
            gst_turn = []
            gst_pen = []
            
        # --- Default Label (Correlation logic) ---
        # Calculate log odds of defaulting
        # Base risk: low income has base 0.1, mid 0.02, high 0.005
        base_risk = {"high": -5.0, "mid": -3.5, "low": -2.0}[inc]
        
        # Add risk factors
        risk_score = base_risk
        
        # Shocks
        if shock_job:
            risk_score += 1.8
        if shock_health:
            risk_score += 1.2
            
        # Utility failures (count lapse months)
        lapses = sum(1 for s in util_status if s == "lapsed")
        risk_score += lapses * 0.6
        
        # Late payments
        lates = sum(1 for s in util_status if s == "late")
        risk_score += lates * 0.2
        
        # Mobile failures
        mob_lapses = sum(1 for s in mob_status if s == "lapsed")
        risk_score += mob_lapses * 0.4
        
        # UPI failures
        total_upi = sum(upi_count)
        total_failed = sum(upi_failed_count)
        if total_upi > 0:
            fail_rate = total_failed / total_upi
            if fail_rate > 0.10:
                risk_score += 1.0
                
        # GST penalties
        if msme:
            gst_lapses = sum(1 for s in gst_stat if s == "unfiled")
            risk_score += gst_lapses * 0.8
            
        # Convert to probability
        default_prob = 1.0 / (1.0 + np.exp(-risk_score))
        default_label = int(np.random.rand() < default_prob)
        
        profile = ApplicantProfile(
            applicant_id=app_id,
            gender=gender,
            geography=geo,
            income_proxy=inc,
            is_msme=msme,
            upi_count=upi_count,
            upi_failed_count=upi_failed_count,
            upi_amount=upi_amount,
            upi_merchant_count=upi_merchant_count,
            upi_night_count=upi_night_count,
            upi_income_deposits=upi_income_deposits,
            utility_status=util_status,
            utility_days_late=util_days_late,
            mobile_recharge_status=mob_status,
            mobile_plan_value=mob_plan,
            gst_status=gst_stat,
            gst_turnover=gst_turn,
            gst_penalties=gst_pen,
            income_shock_job_loss=shock_job,
            income_shock_health=shock_health,
            default_label=default_label
        )
        
        profiles.append(profile.model_dump())
        
    return pd.DataFrame(profiles)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_profiles", type=int, default=None)
    args = parser.parse_args()
    
    config = load_config()
    num = args.num_profiles or config["data"]["num_profiles"]
    seed = config["data"].get("random_seed", 42)
    output_path = config["data"]["synthetic_output_path"]
    
    print(f"Generating {num} synthetic profiles with seed {seed}...")
    df = generate_synthetic_data(num, seed)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Saving to {output_path}...")
    df.to_parquet(output_path, index=False)
    print("Done!")

if __name__ == "__main__":
    main()
