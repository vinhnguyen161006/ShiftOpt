from dataclasses import asdict

from fastapi import APIRouter
from shiftopt.constraints.labor_law_vn import LaborRules

from src.rules.schemas import LaborRulesRead

router = APIRouter(prefix="/labor-rules", tags=["rules"])


@router.get("", response_model=LaborRulesRead)
async def get_labor_rules() -> LaborRulesRead:
    return LaborRulesRead(**asdict(LaborRules()))
