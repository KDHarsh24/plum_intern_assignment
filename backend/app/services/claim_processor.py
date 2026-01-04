"""
Claim Processing Service - Orchestrates OCR, LLM extraction, and adjudication
"""
import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.models import Claim, ClaimStatus
from app.schemas import ClaimSubmission, ExtractedData, AdjudicationResult, ClaimCategory
from app.services.ocr_service import document_processor
from app.services.llm_service import llm_extractor
from app.services.adjudication_engine import adjudication_engine


class ClaimProcessor:
    """Orchestrates the complete claim processing pipeline"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def submit_claim(
        self,
        claim_data: ClaimSubmission,
        document_paths: List[str]
    ) -> Claim:
        """
        Create a new claim record
        """
        claim_id = f"CLM_{uuid.uuid4().hex[:8].upper()}"
        
        claim = Claim(
            claim_id=claim_id,
            patient_name=claim_data.patient_name,
            employee_id=claim_data.employee_id,
            claim_amount=claim_data.claim_amount,
            claim_category=claim_data.claim_category.value,
            treatment_date=claim_data.treatment_date,
            hospital_name=claim_data.hospital_name,
            documents=document_paths,
            status=ClaimStatus.PENDING.value,
            notes=claim_data.notes
        )
        
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        
        return claim
    
    def process_claim(self, claim_id: str) -> AdjudicationResult:
        """
        Full claim processing pipeline:
        1. OCR document extraction
        2. LLM data extraction
        3. Adjudication
        """
        claim = self.db.query(Claim).filter(Claim.claim_id == claim_id).first()
        if not claim:
            raise ValueError(f"Claim not found: {claim_id}")
        
        # Update status to processing
        claim.status = ClaimStatus.PROCESSING.value
        self.db.commit()
        
        try:
            # Step 1: OCR - Extract text from documents
            if claim.documents:
                ocr_text, ocr_confidence = document_processor.process_multiple_documents(
                    claim.documents
                )
                claim.extracted_text = ocr_text
            else:
                ocr_text = ""
                ocr_confidence = 0.5
            
            # Step 2: LLM - Extract structured data
            if ocr_text:
                extracted_data = llm_extractor.extract_medical_data(ocr_text)
            else:
                extracted_data = ExtractedData(confidence=0.3)
            
            # Merge extracted data with claim data
            if extracted_data.patient_name:
                claim.patient_name = extracted_data.patient_name
            if extracted_data.doctor_name:
                claim.doctor_name = extracted_data.doctor_name
            if extracted_data.doctor_reg_number:
                claim.doctor_reg_number = extracted_data.doctor_reg_number
            if extracted_data.hospital_name:
                claim.hospital_name = extracted_data.hospital_name
            if extracted_data.diagnosis:
                claim.diagnosis = extracted_data.diagnosis
            
            claim.extracted_data = extracted_data.model_dump()
            
            # Get YTD claimed amount for this employee
            ytd_claimed = self._get_ytd_claimed(claim.employee_id)
            
            # Get number of claims today (for fraud detection)
            claims_today = self._get_claims_today(claim.employee_id)
            
            # Check if it's a network hospital
            is_network = self._is_network_hospital(claim.hospital_name)
            
            # Step 3: Adjudication
            result = adjudication_engine.adjudicate_claim(
                claim_amount=claim.claim_amount,
                claim_category=claim.claim_category,
                treatment_date=claim.treatment_date or datetime.now(),
                extracted_data=extracted_data,
                ytd_claimed=ytd_claimed,
                is_network_hospital=is_network,
                previous_claims_today=claims_today
            )
            
            # Update claim with result
            claim.status = result.decision.value
            claim.approved_amount = result.approved_amount
            claim.decision_reasons = result.rejection_reasons
            claim.confidence_score = result.confidence_score
            claim.notes = result.notes
            claim.next_steps = result.next_steps
            claim.processed_at = datetime.utcnow()
            claim.ytd_claimed = ytd_claimed + result.approved_amount
            
            self.db.commit()
            self.db.refresh(claim)
            
            return result
            
        except Exception as e:
            claim.status = ClaimStatus.MANUAL_REVIEW.value
            claim.notes = f"Processing error: {str(e)}"
            claim.decision_reasons = ["PROCESSING_ERROR"]
            self.db.commit()
            raise
    
    def _get_ytd_claimed(self, employee_id: str) -> float:
        """Get year-to-date claimed amount for employee"""
        current_year = datetime.now().year
        start_of_year = datetime(current_year, 1, 1)
        
        claims = self.db.query(Claim).filter(
            Claim.employee_id == employee_id,
            Claim.submitted_at >= start_of_year,
            Claim.status.in_([ClaimStatus.APPROVED.value, ClaimStatus.PARTIAL.value])
        ).all()
        
        return sum(c.approved_amount for c in claims)
    
    def _get_claims_today(self, employee_id: str) -> int:
        """Get number of claims submitted today"""
        today = datetime.now().date()
        
        count = self.db.query(Claim).filter(
            Claim.employee_id == employee_id,
            Claim.submitted_at >= datetime.combine(today, datetime.min.time())
        ).count()
        
        return count
    
    def _is_network_hospital(self, hospital_name: str) -> bool:
        """Check if hospital is in network"""
        if not hospital_name:
            return False
        
        network_hospitals = [
            "apollo", "fortis", "max", "manipal", "narayana"
        ]
        
        hospital_lower = hospital_name.lower()
        return any(nh in hospital_lower for nh in network_hospitals)
    
    def get_claim(self, claim_id: str) -> Optional[Claim]:
        """Get a claim by ID"""
        return self.db.query(Claim).filter(Claim.claim_id == claim_id).first()
    
    def get_claims(
        self,
        employee_id: str = None,
        status: str = None,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[Claim], int]:
        """Get claims with optional filtering"""
        query = self.db.query(Claim)
        
        if employee_id:
            query = query.filter(Claim.employee_id == employee_id)
        
        if status:
            query = query.filter(Claim.status == status)
        
        total = query.count()
        
        claims = query.order_by(Claim.submitted_at.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()
        
        return claims, total
    
    def save_uploaded_file(self, file_content: bytes, filename: str, claim_id: str) -> str:
        """Save an uploaded file and return its path"""
        claim_dir = UPLOAD_DIR / claim_id
        claim_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = claim_dir / unique_name
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return str(file_path)
