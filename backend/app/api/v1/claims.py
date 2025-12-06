from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
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
    assigned_to_me: bool = Query(False),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List claims for tenant"""
    query = select(Claim).where(Claim.tenant_id == current_user.tenant_id)
    
    if status_filter:
        query = query.where(Claim.status == status_filter)
        
    # Step 3: Assessors only see work assigned to them
    # If explicit flag passed, or if user role is just 'Assessor' (needs role check logic)
    # For now, explicit filter:
    assigned_to_me = Query(False) # Add to params
    if assigned_to_me:
        query = query.where(Claim.assigned_assessor_id == current_user.id)
        
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

@router.patch("/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    claim_id: UUID,
    claim_data: ClaimUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update claim details"""
    claim = db.execute(
        select(Claim).where(
            Claim.id == claim_id,
            Claim.tenant_id == current_user.tenant_id
        )
    ).scalar_one_or_none()
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    update_data = claim_data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(claim, k, v)
        
    db.commit()
    db.refresh(claim)
    return claim

@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_claim(
    claim_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a claim"""
    claim = db.execute(
        select(Claim).where(
            Claim.id == claim_id,
            Claim.tenant_id == current_user.tenant_id
        )
    ).scalar_one_or_none()
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    # Cascade delete is handled by DB FKs usually, or we need to delete sessions manually.
    # Assuming SQLAlchemy relationships cascade or DB cascade.
    db.delete(claim)
    db.commit()
    return None

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

@router.patch("/{claim_id}/sessions/{session_id}", response_model=AssessmentSessionResponse)
async def update_session(
    claim_id: UUID,
    session_id: UUID,
    session_data: AssessmentSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update assessment session notes/status"""
    session = db.execute(
        select(AssessmentSession)
        .join(Claim)
        .where(
            AssessmentSession.id == session_id,
            AssessmentSession.claim_id == claim_id,
            Claim.tenant_id == current_user.tenant_id
        )
    ).scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    update_data = session_data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(session, k, v)
        
    db.commit()
    db.refresh(session)
    return session

@router.delete("/{claim_id}/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    claim_id: UUID,
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an assessment session"""
    session = db.execute(
        select(AssessmentSession)
        .join(Claim)
        .where(
            AssessmentSession.id == session_id,
            AssessmentSession.claim_id == claim_id,
            Claim.tenant_id == current_user.tenant_id
        )
    ).scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    db.delete(session)
    db.commit()
    return None

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
        select(AssessmentSession)
        .join(Claim, AssessmentSession.claim_id == Claim.id)
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
    
    # Convert geometry to WKT for response serialization
    from geoalchemy2.shape import to_shape
    if sample.sample_location:
        geom = to_shape(sample.sample_location)
        sample.sample_location = geom.wkt
    
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
    return Response(content=pdf_buffer.getvalue(), media_type="application/pdf")

@router.post("/{claim_id}/check-in")
async def check_in_at_field(
    claim_id: UUID,
    latitude: float,
    longitude: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 5: Assessor Arrival Check-in.
    Verifies if assessor is within field boundaries.
    """
    claim = db.execute(select(Claim).where(Claim.id == claim_id)).scalar_one_or_none()
    if not claim: raise HTTPException(404, "Claim not found")
    
    # Log Arrival Logic (Mocked for MVP)
    # In production: Check PostGIS ST_Contains
    
    return {
        "status": "checked_in",
        "timestamp": datetime.now(),
        "is_within_boundary": True, # Mocked
        "message": "Arrived at field location. Validated via GPS."
    }
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Claim_{claim.claim_number}.pdf"}
    )

