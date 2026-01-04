from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class ClaimStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PARTIAL = "PARTIAL"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class ClaimCategory(str, Enum):
    CONSULTATION = "consultation"
    DIAGNOSTIC = "diagnostic"
    PHARMACY = "pharmacy"
    DENTAL = "dental"
    VISION = "vision"
    ALTERNATIVE = "alternative"


class ClaimSubmission(BaseModel):
    patient_name: str
    employee_id: str
    claim_amount: float
    claim_category: ClaimCategory
    treatment_date: datetime
    hospital_name: Optional[str] = None
    notes: Optional[str] = None


class ExtractedData(BaseModel):
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_reg_number: Optional[str] = None
    hospital_name: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_date: Optional[str] = None
    medicines: Optional[List[str]] = []
    tests: Optional[List[str]] = []
    total_amount: Optional[float] = None
    bill_items: Optional[List[dict]] = []
    confidence: float = 0.0


class AdjudicationResult(BaseModel):
    claim_id: str
    decision: ClaimStatus
    approved_amount: float = 0.0
    rejection_reasons: List[str] = []
    confidence_score: float = 0.0
    notes: str = ""
    next_steps: str = ""
    breakdown: Optional[dict] = None


class ClaimResponse(BaseModel):
    id: int
    claim_id: str
    patient_name: str
    employee_id: str
    claim_amount: float
    approved_amount: float
    claim_category: str
    treatment_date: Optional[datetime]
    status: str
    decision_reasons: List[str]
    confidence_score: float
    notes: Optional[str]
    next_steps: Optional[str]
    submitted_at: datetime
    processed_at: Optional[datetime]
    extracted_data: Optional[dict]
    
    class Config:
        from_attributes = True


class ClaimListResponse(BaseModel):
    claims: List[ClaimResponse]
    total: int
    page: int
    page_size: int
