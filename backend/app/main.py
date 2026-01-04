"""
FastAPI Main Application - OPD Claim Adjudication System
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
import os

from sqlalchemy.orm import Session

from app.models import init_db, get_db, Claim
from app.schemas import (
    ClaimSubmission, ClaimResponse, ClaimListResponse,
    AdjudicationResult, ClaimCategory, ClaimStatus
)
from app.services.claim_processor import ClaimProcessor
from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Plum OPD Claim Adjudication",
    description="AI-powered OPD insurance claim processing system",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Plum OPD Claim Adjudication",
        "version": "1.0.0"
    }


@app.post("/api/claims/submit", response_model=ClaimResponse)
async def submit_claim(
    patient_name: str = Form(...),
    employee_id: str = Form(...),
    claim_amount: float = Form(...),
    claim_category: ClaimCategory = Form(...),
    treatment_date: str = Form(...),
    hospital_name: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    documents: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Submit a new OPD claim with documents
    """
    # Validate files
    document_paths = []
    
    if documents:
        for doc in documents:
            if doc.filename:
                # Check extension
                ext = os.path.splitext(doc.filename)[1].lower()
                if ext not in ALLOWED_EXTENSIONS:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File type {ext} not allowed. Allowed: {ALLOWED_EXTENSIONS}"
                    )
                
                # Check size
                content = await doc.read()
                if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Max size: {MAX_FILE_SIZE_MB}MB"
                    )
                
                # Reset file position for later read
                await doc.seek(0)
    
    # Parse treatment date
    try:
        treatment_dt = datetime.fromisoformat(treatment_date.replace('Z', '+00:00'))
    except ValueError:
        try:
            treatment_dt = datetime.strptime(treatment_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Create claim submission
    claim_data = ClaimSubmission(
        patient_name=patient_name,
        employee_id=employee_id,
        claim_amount=claim_amount,
        claim_category=claim_category,
        treatment_date=treatment_dt,
        hospital_name=hospital_name,
        notes=notes
    )
    
    processor = ClaimProcessor(db)
    
    # Create claim first to get ID
    claim = processor.submit_claim(claim_data, [])
    
    # Save uploaded files
    if documents:
        for doc in documents:
            if doc.filename:
                content = await doc.read()
                file_path = processor.save_uploaded_file(content, doc.filename, claim.claim_id)
                document_paths.append(file_path)
        
        # Update claim with document paths
        claim.documents = document_paths
        db.commit()
    
    return ClaimResponse(
        id=claim.id,
        claim_id=claim.claim_id,
        patient_name=claim.patient_name,
        employee_id=claim.employee_id,
        claim_amount=claim.claim_amount,
        approved_amount=claim.approved_amount,
        claim_category=claim.claim_category,
        treatment_date=claim.treatment_date,
        status=claim.status,
        decision_reasons=claim.decision_reasons or [],
        confidence_score=claim.confidence_score,
        notes=claim.notes,
        next_steps=claim.next_steps,
        submitted_at=claim.submitted_at,
        processed_at=claim.processed_at,
        extracted_data=claim.extracted_data
    )


@app.post("/api/claims/{claim_id}/process", response_model=AdjudicationResult)
async def process_claim(claim_id: str, db: Session = Depends(get_db)):
    """
    Process a pending claim through the adjudication pipeline
    """
    processor = ClaimProcessor(db)
    
    claim = processor.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if claim.status not in [ClaimStatus.PENDING.value, ClaimStatus.PROCESSING.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Claim already processed. Status: {claim.status}"
        )
    
    try:
        result = processor.process_claim(claim_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/claims/{claim_id}", response_model=ClaimResponse)
async def get_claim(claim_id: str, db: Session = Depends(get_db)):
    """
    Get a specific claim by ID
    """
    processor = ClaimProcessor(db)
    claim = processor.get_claim(claim_id)
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return ClaimResponse(
        id=claim.id,
        claim_id=claim.claim_id,
        patient_name=claim.patient_name,
        employee_id=claim.employee_id,
        claim_amount=claim.claim_amount,
        approved_amount=claim.approved_amount,
        claim_category=claim.claim_category,
        treatment_date=claim.treatment_date,
        status=claim.status,
        decision_reasons=claim.decision_reasons or [],
        confidence_score=claim.confidence_score,
        notes=claim.notes,
        next_steps=claim.next_steps,
        submitted_at=claim.submitted_at,
        processed_at=claim.processed_at,
        extracted_data=claim.extracted_data
    )


@app.get("/api/claims", response_model=ClaimListResponse)
async def list_claims(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """
    List claims with optional filtering
    """
    processor = ClaimProcessor(db)
    claims, total = processor.get_claims(
        employee_id=employee_id,
        status=status,
        page=page,
        page_size=page_size
    )
    
    claim_responses = [
        ClaimResponse(
            id=c.id,
            claim_id=c.claim_id,
            patient_name=c.patient_name,
            employee_id=c.employee_id,
            claim_amount=c.claim_amount,
            approved_amount=c.approved_amount,
            claim_category=c.claim_category,
            treatment_date=c.treatment_date,
            status=c.status,
            decision_reasons=c.decision_reasons or [],
            confidence_score=c.confidence_score,
            notes=c.notes,
            next_steps=c.next_steps,
            submitted_at=c.submitted_at,
            processed_at=c.processed_at,
            extracted_data=c.extracted_data
        )
        for c in claims
    ]
    
    return ClaimListResponse(
        claims=claim_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@app.get("/api/policy")
async def get_policy():
    """
    Get current policy terms
    """
    from app.services.adjudication_engine import PolicyTerms
    policy = PolicyTerms()
    return policy.policy_data


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Get claim statistics
    """
    total = db.query(Claim).count()
    approved = db.query(Claim).filter(Claim.status == ClaimStatus.APPROVED.value).count()
    rejected = db.query(Claim).filter(Claim.status == ClaimStatus.REJECTED.value).count()
    partial = db.query(Claim).filter(Claim.status == ClaimStatus.PARTIAL.value).count()
    pending = db.query(Claim).filter(Claim.status == ClaimStatus.PENDING.value).count()
    manual_review = db.query(Claim).filter(Claim.status == ClaimStatus.MANUAL_REVIEW.value).count()
    
    total_claimed = db.query(Claim).with_entities(
        db.query(Claim).with_entities(Claim.claim_amount).as_scalar()
    ).scalar() or 0
    
    return {
        "total_claims": total,
        "approved": approved,
        "rejected": rejected,
        "partial": partial,
        "pending": pending,
        "manual_review": manual_review,
        "approval_rate": (approved + partial) / total * 100 if total > 0 else 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
