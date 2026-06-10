# Synthetic Profile Generation Methodology

This directory contains scripts for generating synthetic credit profiles of unbanked individuals, calibrated to the socio-demographic context of India.

## 1. Socio-Demographic Calibrations
The core customer demographics are sampled using probabilities derived from the **World Bank Global Findex Database (India)**:
- **Gender**: M (52%), F (48%)
- **Geography Tier**: Urban (30%), Semi-urban (35%), Rural (35%)
- **Income Proxy**: High (20%), Mid (50%), Low (30%)
- **MSME Flag**: 20% of profiles are designated as micro-merchants/MSMEs, which activates GST signals.

## 2. Signal Generation Model
To simulate realistic transaction behaviors, we model several alternative data pathways:

### UPI Transactions
- **Monthly Count**: Modeled as a Poisson process where the parameter $\lambda$ is sampled from a Beta distribution ($B(3, 2) \times 40$) representing transactional habit. It is scaled by the income proxy of the user.
- **Transaction Amount**: Calibrated based on income tier. High income averages ₹1200 per transaction, mid averages ₹450, and low averages ₹150.
- **Merchant Diversity**: Modeled as Poisson-distributed subset count of total transactions.
- **Night Transaction Share**: Calculated by binomial sampling with a 15% probability of transacting between 10 PM and 6 AM.
- **Failed Transactions**: Modeled binomially, where high-risk profiles have a higher failure rate (e.g. 12% vs 4%) to simulate cash-flow issues or connectivity issues.

### Utility & Mobile Payment Streaks
- Modeled via a **3-state Markov chain** (States: `on_time` → `late` → `lapsed`).
- Transition probabilities are calibrated differently based on the underlying creditworthiness of the user:
  - **Creditworthy Transition Matrix**:
    $$P_{good} = \begin{pmatrix} 0.90 & 0.08 & 0.02 \\ 0.60 & 0.30 & 0.10 \\ 0.30 & 0.30 & 0.40 \end{pmatrix}$$
  - **High-Risk Transition Matrix**:
    $$P_{bad} = \begin{pmatrix} 0.60 & 0.30 & 0.10 \\ 0.40 & 0.40 & 0.20 \\ 0.15 & 0.25 & 0.60 \end{pmatrix}$$

### Income Shock Events
- **Job Loss**: Occurs with a yearly probability of 8% (`income_shock_job_loss`).
- **Health Emergency**: Occurs with a yearly probability of 5% (`income_shock_health`).
- Experiencing a shock stochastically increases default probability and increases the likelihood of transition to "late" or "lapsed" payment states.

### Default Label
A ground truth `default_label` (binary) is simulated based on the log-odds combination of income level, shock history, number of utility and mobile payment lapses, UPI failure rates, and GST late-filings. This provides a realistic correlation target for training supervised models.
