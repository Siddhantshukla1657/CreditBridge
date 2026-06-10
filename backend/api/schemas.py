from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ApplicantInput(BaseModel):
    applicant_id: Optional[str] = None
    gender: str = Field(..., description="M or F")
    geography: str = Field(..., description="urban, semi-urban, or rural")
    income_proxy: str = Field(..., description="high, mid, or low")
    is_msme: bool = Field(..., description="True if applicant is an MSME")
    
    # UPI monthly signals (12 elements, from oldest m1 to newest m12)
    upi_count: List[int] = Field(..., min_length=12, max_length=12)
    upi_failed_count: List[int] = Field(..., min_length=12, max_length=12)
    upi_amount: List[float] = Field(..., min_length=12, max_length=12)
    upi_merchant_count: List[int] = Field(..., min_length=12, max_length=12)
    upi_night_count: List[int] = Field(..., min_length=12, max_length=12)
    upi_income_deposits: List[int] = Field(..., min_length=12, max_length=12)
    
    # Utility billing signals (12 elements)
    utility_status: List[str] = Field(..., min_length=12, max_length=12)
    utility_days_late: List[float] = Field(..., min_length=12, max_length=12)
    
    # Mobile recharge signals (12 elements)
    mobile_recharge_status: List[str] = Field(..., min_length=12, max_length=12)
    mobile_plan_value: List[float] = Field(..., min_length=12, max_length=12)
    
    # GST signals (optional or 12 elements for MSMEs)
    gst_status: Optional[List[str]] = Field(default_factory=list)
    gst_turnover: Optional[List[float]] = Field(default_factory=list)
    gst_penalties: Optional[List[float]] = Field(default_factory=list)
    
    # Shocks
    income_shock_job_loss: bool = False
    income_shock_health: bool = False

class FactorItem(BaseModel):
    feature: str
    label: str
    points: int
    text: str

class WaterfallItem(BaseModel):
    name: str
    value: float
    start: float
    end: float
    is_total: bool

class ForceFeatureItem(BaseModel):
    """Single feature entry in a SHAP force plot."""
    name: str
    shap_value: float
    feature_value: Optional[Any] = None
    direction: str  # "positive" | "negative"

class ForcePlotData(BaseModel):
    """Structured SHAP force-plot payload served by the API."""
    base_value: float
    output_value: float
    features: List[ForceFeatureItem]
    positive_features: List[ForceFeatureItem]
    negative_features: List[ForceFeatureItem]

class ScoreResponse(BaseModel):
    applicant_id: str
    score: int
    band: str
    default_probability: float
    confidence: float
    top_factors: List[FactorItem]
    waterfall_data: List[WaterfallItem]
    force_plot_data: Optional[ForcePlotData] = None
    fairness_flags: List[str]
    model_version: str
