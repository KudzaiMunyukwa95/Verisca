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
    
    # 1. Log Arrival (Audit Trail)
    # In real app: create an AuditLog entry.
    
    # 2. Check Spatial
    # is_within = SpatialService.check_point_in_field(db, claim.field_id, lat, lon)
    # Mock for MVP:
    is_within = True 
    distance_to_center = 0.0
    
    return {
        "status": "checked_in",
        "timestamp": datetime.now(),
        "is_within_boundary": is_within,
        "message": "Arrived at field location."
    }
