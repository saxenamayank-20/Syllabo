from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.schemas.ai import GeneratePlanRequest, PlanPreview, SavePlanRequest, SavePlanResponse
from app.services import plan_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate-plan", response_model=PlanPreview)
def generate_plan(
    data: GeneratePlanRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> PlanPreview:
    """Ask Gemini for a plan and return a validated preview. Nothing is saved yet."""
    return plan_service.generate_preview(db, user, data)


@router.post("/save-plan", response_model=SavePlanResponse)
def save_plan(
    data: SavePlanRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> SavePlanResponse:
    """Save a previewed plan. Replaces only pending AI tasks in the same date range."""
    return plan_service.save_plan(db, user, data)
