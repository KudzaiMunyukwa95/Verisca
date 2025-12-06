
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.orchestrator import AssessmentOrchestrator
from app.schemas.intelligence import ComprehensiveAssessmentRequest, ComprehensiveAssessmentResult

router = APIRouter()

@router.post("/comprehensive", response_model=ComprehensiveAssessmentResult)
async def create_comprehensive_assessment(
    request: ComprehensiveAssessmentRequest,
    db: Session = Depends(get_db)
):
    """
    **Verisca Intelligence Engine**
    
    Performs a multi-method, scientifically validated, economically optimized assessment.
    
    Features:
    - **Intelligent Method Routing**: Auto-selects USDA method based on peril/stage.
    - **Fraud/Error Detection**: Statistical CV and Z-Score analysis.
    - **Economic Strategy**: Compares Grain vs Silage outcomes if market data provided.
    """
    try:
        result = await AssessmentOrchestrator.perform_comprehensive_assessment(db, request)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
