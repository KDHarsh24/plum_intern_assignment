from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Enum as SQLEnum, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

from app.config import DATABASE_URL

Base = declarative_base()


class ClaimStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PARTIAL = "PARTIAL"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(50), unique=True, index=True)
    
    # Claimant info
    patient_name = Column(String(200))
    employee_id = Column(String(50))
    policy_id = Column(String(50), default="PLUM_OPD_2024")
    
    # Claim details
    claim_amount = Column(Float, default=0.0)
    approved_amount = Column(Float, default=0.0)
    claim_category = Column(String(50))  # consultation, diagnostic, pharmacy, dental, vision, alternative
    
    # Treatment info
    treatment_date = Column(DateTime)
    diagnosis = Column(Text)
    doctor_name = Column(String(200))
    doctor_reg_number = Column(String(50))
    hospital_name = Column(String(200))
    
    # Documents
    documents = Column(JSON, default=list)  # List of uploaded file paths
    extracted_text = Column(Text)  # Raw OCR text
    extracted_data = Column(JSON)  # Structured extracted data
    
    # Decision
    status = Column(String(20), default=ClaimStatus.PENDING.value)
    decision_reasons = Column(JSON, default=list)
    confidence_score = Column(Float, default=0.0)
    notes = Column(Text)
    next_steps = Column(Text)
    
    # Timestamps
    submitted_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # For tracking limits
    ytd_claimed = Column(Float, default=0.0)  # Year-to-date claimed amount


# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
