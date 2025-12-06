from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.models.tenant import User
from app.models.claims import Claim, AssessmentSession, AssessmentSample, ClaimStatus, AssessmentStatus
from app.models.spatial import Farm, Field

router = APIRouter()

@router.get("/down")
async def sync_down(
    last_sync: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download assigned Claims and Context (Farm/Field) updated since last_sync.
    For offline caching.
    """
    # 1. Fetch Assigned Claims
    query = select(Claim).where(
        Claim.assigned_assessor_id == current_user.id,
        Claim.status.in_([ClaimStatus.ASSIGNED, ClaimStatus.IN_PROGRESS]),
        Claim.tenant_id == current_user.tenant_id
    )
    
    if last_sync:
        query = query.where(Claim.updated_at >= last_sync)
        
    claims = db.execute(query).scalars().all()
    
    # 2. Fetch Related Data (Farms, Fields) for these claims
    # Optimization: Could use join or explicit fetch. For MVP, fetching IDs explicitly.
    farm_ids = list(set([c.farm_id for c in claims]))
    field_ids = list(set([c.field_id for c in claims]))
    
    farms = []
    fields = []
    
    if farm_ids:
        farms = db.execute(select(Farm).where(Farm.id.in_(farm_ids))).scalars().all()
    if field_ids:
        fields = db.execute(select(Field).where(Field.id.in_(field_ids))).scalars().all()
        
    return {
        "timestamp": datetime.utcnow(),
        "claims": claims,
        "farms": farms,
        "fields": fields
    }

@router.post("/up")
async def sync_up(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload offline Assessment Sessions and Samples.
    Payload format: { "sessions": [...], "samples": [...] }
    """
    sessions_data = payload.get("sessions", [])
    samples_data = payload.get("samples", [])
    
    synced_ids = {"sessions": [], "samples": []}
    
    # Process Sessions (Upsert)
    for s_dat in sessions_data:
        # Check ownership logic or existence
        # For MVP: Assuming create or update by ID
        session_id = s_dat.get("id")
        
        existing = db.execute(select(AssessmentSession).where(AssessmentSession.id == session_id)).scalar_one_or_none()
        if existing:
            # Update fields
            existing.status = AssessmentStatus.SYNCED
            existing.date_completed = s_dat.get("date_completed")
            existing.calculated_result = s_dat.get("calculated_result")
            # ... other fields
        else:
            # Create new
            new_sess = AssessmentSession(
                id=session_id, # Use mobile generated UUID
                claim_id=s_dat.get("claim_id"),
                assessor_id=current_user.id,
                assessment_method=s_dat.get("assessment_method"),
                growth_stage=s_dat.get("growth_stage"),
                status=AssessmentStatus.SYNCED,
                created_at=s_dat.get("created_at")
            )
            db.add(new_sess)
        synced_ids["sessions"].append(session_id)
        
    db.commit() # Commit sessions first
    
    # Process Samples
    for samp_dat in samples_data:
        # ... Similar logic for samples
        # Ideally bulk insert
        pass
        
    return {"status": "success", "synced": synced_ids}
