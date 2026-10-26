from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from shiftopt.staffing.linear import (
    DEFAULT_ALPHA,
    DEFAULT_MIN_STAFF,
    DEFAULT_NIGHT_MIN_STAFF,
    DEFAULT_PRODUCTIVITY,
)

from src.demand.models import DemandSource, StaffingMode

HOURS_PER_WEEK = 168


class ConversionParams(BaseModel):
    alpha: float = Field(DEFAULT_ALPHA, gt=0)
    productivity: float = Field(DEFAULT_PRODUCTIVITY, gt=0)
    min_staff: int = Field(DEFAULT_MIN_STAFF, ge=0)
    night_min_staff: int = Field(DEFAULT_NIGHT_MIN_STAFF, ge=0)


class DemandProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    source: DemandSource = DemandSource.MANUAL
    mode: StaffingMode = StaffingMode.LINEAR
    required_staff: list[int] = Field(min_length=HOURS_PER_WEEK, max_length=HOURS_PER_WEEK)
    conversion_params: ConversionParams = Field(default_factory=ConversionParams)


class DemandProfileUpdate(DemandProfileCreate):
    pass


class DemandProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    source: DemandSource
    mode: StaffingMode
    required_staff: list[int]
    conversion_params: dict[str, float]
    created_at: datetime


class DatasetDemandRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    store_id: int
    conversion_params: ConversionParams = Field(default_factory=ConversionParams)
