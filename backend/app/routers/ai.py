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
    """get a plan from gemini and return a checked preview, nothing saved yet"""
    return plan_service.generate_preview(db, user, data)


@router.post("/save-plan", response_model=SavePlanResponse)
def save_plan(
    data: SavePlanRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> SavePlanResponse:
    """save the plan, only replaces pending ai tasks in that range"""
    return plan_service.save_plan(db, user, data)
