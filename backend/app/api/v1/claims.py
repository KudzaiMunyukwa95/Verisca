from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.models.tenant import User
from app.models.claims import Claim, AssessmentSession, AssessmentSample, ClaimStatus, AssessmentStatus
from app.schemas.claims import (
    ClaimCreate, ClaimUpdate, ClaimResponse,
    AssessmentSessionCreate, AssessmentSessionUpdate, AssessmentSessionResponse,
    AssessmentSampleCreate, AssessmentSampleResponse
)
from app.models.spatial import Farm, Field

router = APIRouter()

# --- Claims Endpoints ---

@router.post("/", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    claim_data: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report a new claim"""
    # Verify Farm/Field ownership
    farm = db.execute(
        select(Farm).where(
            Farm.id == claim_data.farm_id,
            Farm.tenant_id == current_user.tenant_id
        )
    ).scalar_one_or_none()
    
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    # Generate claim number (simple logic for now, could be improved)
    # Format: CLM-{Year}-{Random/Seq}
    year = datetime.now().year
    count = db.query(Claim).filter(Claim.tenant_id == current_user.tenant_id).count()
    claim_number = f"CLM-{year}-{count+1:05d}"
    
    db_obj = Claim(
        tenant_id=current_user.tenant_id,
        claim_number=claim_number,
        farm_id=claim_data.farm_id,
        field_id=claim_data.field_id,
        peril_type=claim_data.peril_type,
        date_of_loss=claim_data.date_of_loss,
        loss_description=claim_data.loss_description,
        created_by_user_id=current_user.id,
        status=ClaimStatus.REPORTED
    )
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/", response_model=List[ClaimResponse])
async def list_claims(
    status_filter: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List claims for tenant"""
    query = select(Claim).where(Claim.tenant_id == current_user.tenant_id)
    
    if status_filter:
        query = query.where(Claim.status == status_filter)
        
    query = query.order_by(desc(Claim.created_at)).offset(skip).limit(limit)
    return db.execute(query).scalars().all()

@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    claim = db.execute(
        select(Claim).where(
            Claim.id == claim_id, 
            Claim.tenant_id == current_user.tenant_id
        )
    ).scalar_one_or_none()
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim

# --- Assessment Sessions Endpoints ---

@router.post("/{claim_id}/sessions", response_model=AssessmentSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment_session(
    claim_id: UUID,
    session_data: AssessmentSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new assessment session"""
    # Verify Claim exists
    claim = db.execute(
        select(Claim).where(
            Claim.id == claim_id,
            Claim.tenant_id == current_user.tenant_id
        )
    ).scalar_one_or_none()
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    session = AssessmentSession(
        claim_id=claim_id,
        assessor_id=current_user.id,
        assessment_method=session_data.assessment_method,
        growth_stage=session_data.growth_stage,
        weather_conditions=session_data.weather_conditions,
        crop_conditions=session_data.crop_conditions,
        assessor_notes=session_data.assessor_notes,
        status=AssessmentStatus.IN_PROGRESS
    )
    
    db.add(session)
    
    # Update claim status
    if claim.status == ClaimStatus.ASSIGNED or claim.status == ClaimStatus.REPORTED:
         claim.status = ClaimStatus.IN_PROGRESS
         db.add(claim)
         
    db.commit()
    db.refresh(session)
    return session

@router.get("/{claim_id}/sessions", response_model=List[AssessmentSessionResponse])
async def list_sessions(
    claim_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    claim = db.execute(
        select(Claim).where(Claim.id == claim_id, Claim.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()
    
    if not claim:
         raise HTTPException(status_code=404, detail="Claim not found")
         
    sessions = db.execute(
        select(AssessmentSession)
        .where(AssessmentSession.claim_id == claim_id)
        .options(selectinload(AssessmentSession.samples))
        .order_by(desc(AssessmentSession.created_at))
    ).scalars().all()
    
    return sessions

@router.post("/sessions/{session_id}/samples", response_model=AssessmentSampleResponse)
async def add_sample(
    session_id: UUID,
    sample_data: AssessmentSampleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record a sample point"""
    # Verify session access via claim -> tenant
    session = db.execute(
        select(AssessmentSession).join(Claim)
        .where(
            AssessmentSession.id == session_id,
            Claim.tenant_id == current_user.tenant_id
        )
    ).scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Create sample
    location_wkt = f"POINT({sample_data.lng} {sample_data.lat})"
    
    sample = AssessmentSample(
        session_id=session_id,
        sample_number=sample_data.sample_number,
        sample_location=location_wkt,
        gps_accuracy_meters=sample_data.gps_accuracy_meters,
        timestamp=sample_data.timestamp or datetime.utcnow(),
        measurements=sample_data.measurements,
        evidence_refs=sample_data.evidence_refs,
        notes=sample_data.notes
    )
    
    db.add(sample)
    db.commit()
    db.refresh(sample)
    
    # Handle WKT response if needed
    # For now relying on Pydantic or basic serialization
    return sample

# --- Reporting ---
from fastapi.responses import StreamingResponse
from app.services.reporting import ReportService

@router.get("/{claim_id}/report")
async def generate_claim_report(
    claim_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate PDF Assessment Report.
    """
    # 1. Fetch Claim
    claim = db.execute(
        select(Claim).where(Claim.id == claim_id, Claim.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()
    
    if not claim:
         raise HTTPException(status_code=404, detail="Claim not found")
         
    # 2. Fetch Sessions & Samples
    sessions = db.execute(
        select(AssessmentSession)
        .where(AssessmentSession.claim_id == claim_id)
        .options(selectinload(AssessmentSession.samples))
        .order_by(desc(AssessmentSession.created_at))
    ).scalars().all()
    
    # 3. Prepare Data
    claim_dict = {
        "claim_number": claim.claim_number,
        "status": claim.status,
        "date_of_loss": claim.date_of_loss,
        "peril_type": claim.peril_type,
        "farm_id": str(claim.farm_id),
        "field_id": str(claim.field_id)
    }
    
    session_dicts = []
    for sess in sessions:
        s_dict = {
            "date_started": str(sess.date_started),
            "assessment_method": sess.assessment_method,
            "calculated_result": sess.calculated_result,
            "samples": []
        }
        for samp in sess.samples:
            s_dict["samples"].append({
                "sample_number": samp.sample_number,
                "sample_location": samp.sample_location, # WKT/Geometry
                "measurements": samp.measurements,
                "notes": samp.notes
            })
        session_dicts.append(s_dict)
        
    # 4. Generate PDF
    pdf_buffer = ReportService.generate_assessment_report(claim_dict, session_dicts)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Claim_{claim.claim_number}.pdf"}
    )

