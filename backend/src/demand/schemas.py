from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator
from shiftopt.staffing.linear import (
    DEFAULT_ALPHA,
    DEFAULT_MIN_STAFF,
    DEFAULT_NIGHT_MIN_STAFF,
    DEFAULT_PRODUCTIVITY,
)
from shiftopt.time_grid import HOURS_PER_WEEK

from src.demand.models import DemandSource, StaffingMode

MAX_HOURLY_DEMAND = 1000


class ConversionParams(BaseModel):
    alpha: float = Field(DEFAULT_ALPHA, gt=0)
    productivity: float = Field(DEFAULT_PRODUCTIVITY, gt=0)
    min_staff: int = Field(DEFAULT_MIN_STAFF, ge=0)
    night_min_staff: int = Field(DEFAULT_NIGHT_MIN_STAFF, ge=0)


class DemandProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    source: DemandSource = DemandSource.MANUAL
    mode: StaffingMode = StaffingMode.LINEAR
    required_staff: list[Annotated[StrictInt, Field(ge=0, le=MAX_HOURLY_DEMAND)]] = Field(
        min_length=HOURS_PER_WEEK, max_length=HOURS_PER_WEEK
    )
    conversion_params: ConversionParams = Field(default_factory=ConversionParams)

    @field_validator("required_staff", mode="before")
    @classmethod
    def check_cell_count(cls, value: object) -> object:
        if isinstance(value, list) and len(value) != HOURS_PER_WEEK:
            raise ValueError(f"demand grid must have {HOURS_PER_WEEK} cells")
        return value


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
