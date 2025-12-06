from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.models.tenant import User
from app.models.evidence import Evidence
from app.services.files import FileService

router = APIRouter()

# Schema (Simple, inside file for now or move to schemas later)
class EvidenceResponse(BaseModel):
    id: UUID
    filename: str
    url: str
    content_type: str
    created_at: datetime
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.post("/upload", response_model=EvidenceResponse)
async def upload_evidence(
    file: UploadFile = File(...),
    claim_id: Optional[UUID] = Form(None),
    session_id: Optional[UUID] = Form(None),
    location_lat: Optional[float] = Form(None),
    location_lng: Optional[float] = Form(None),
    gps_accuracy: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None), # comma-separated
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload an evidence file (photo/doc).
    """
    # 1. Save File
    file_meta = await FileService.save_upload(file)
    
    # Create Geometry if coords provided
    loc_wkt = None
    if location_lat is not None and location_lng is not None:
        loc_wkt = f"POINT({location_lng} {location_lat})"
    
    # 2. Create DB Record
    db_obj = Evidence(
        tenant_id=current_user.tenant_id,
        uploaded_by_id=current_user.id,
        claim_id=claim_id,
        session_id=session_id,
        location=loc_wkt,
        gps_accuracy_meters=gps_accuracy,
        filename=file_meta["filename"],
        stored_filename=file_meta["stored_filename"],
        file_path=file_meta["file_path"],
        content_type=file_meta["content_type"],
        file_size_bytes=file_meta["file_size"],
        url=file_meta["url"],
        description=description,
        tags=[t.strip() for t in tags.split(",")] if tags else []
    )
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    return db_obj

@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ev = db.query(Evidence).filter(
        Evidence.id == evidence_id,
        Evidence.tenant_id == current_user.tenant_id
    ).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return ev
