from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class FitBreakdown(BaseModel):
    company_size_score: int = Field(default=0, ge=0, le=15, description="Score based on employee count/scale (0-15)")
    seniority_score: int = Field(default=0, ge=0, le=20, description="Score based on decision-making authority (0-20)")
    industry_fit_score: int = Field(default=0, ge=0, le=15, description="Score based on ICP industry alignment (0-15)")
    fit_summary: str = Field(default="", description="Summary of fit strengths/gaps")


class IntentBreakdown(BaseModel):
    behavior_signal_score: int = Field(default=0, ge=0, le=25, description="Score for high-value actions e.g. demo request (0-25)")
    urgency_timeline_score: int = Field(default=0, ge=0, le=15, description="Score for timeline urgency (0-15)")
    budget_readiness_score: int = Field(default=0, ge=0, le=10, description="Score for budget allocation/authority (0-10)")
    intent_summary: str = Field(default="", description="Summary of intent and urgency indicators")


class LeadEvaluation(BaseModel):
    fit_score: int = Field(ge=0, le=50, description="Total Fit score (0-50)")
    intent_score: int = Field(ge=0, le=50, description="Total Intent score (0-50)")
    total_score: int = Field(ge=0, le=100, description="Combined total score (0-100)")
    tier: Literal["HOT", "WARM", "COLD"] = Field(description="Assigned qualification tier")
    fit_breakdown: Optional[FitBreakdown] = Field(default=None, description="Detailed sub-score breakdown for Fit")
    intent_breakdown: Optional[IntentBreakdown] = Field(default=None, description="Detailed sub-score breakdown for Intent")
    key_positive_signals: List[str] = Field(default_factory=list, description="List of notable positive conversion signals")
    red_flags: List[str] = Field(default_factory=list, description="Any disqualifiers or cautionary risks identified")
    rationale: str = Field(description="Comprehensive reasoning explaining the evaluation and score")
    next_action: str = Field(description="Specific, actionable next step for the sales or marketing team")
    sla_response_time: str = Field(default="Within 24 hours", description="Recommended SLA window (e.g., 1 hour, 24 hours, 7-day drip)")

    @field_validator("tier", mode="before")
    @classmethod
    def normalize_tier(cls, v: str) -> str:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in ("HOT", "WARM", "COLD"):
                return v_upper
        return "COLD"


class LeadInput(BaseModel):
    id: str = Field(default="L-UNKNOWN", description="Unique lead identifier")
    name: str = Field(default="Unknown", description="Contact name")
    company: str = Field(default="Unknown", description="Company name")
    company_size: Optional[str] = Field(default="Unknown", description="Company employee size range")
    job_title: Optional[str] = Field(default="Unknown", description="Job title / role")
    industry: Optional[str] = Field(default="Unknown", description="Industry or business domain")
    email: Optional[str] = Field(default="", description="Email address")
    intent_signals: Optional[str] = Field(default="", description="Observed behavioral signals")
    notes: Optional[str] = Field(default="", description="Qualitative notes or form message")
    budget_status: Optional[str] = Field(default="Unknown", description="Budget allocation status")
    timeline: Optional[str] = Field(default="Unknown", description="Implementation timeline")


class RawInboundEmail(BaseModel):
    id: str = Field(default="EM-UNKNOWN", description="Inbound email ID")
    subject: str = Field(default="", description="Email subject line")
    sender: str = Field(default="", description="Sender name and email")
    body: str = Field(default="", description="Raw email text body")
