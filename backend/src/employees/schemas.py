from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator
from shiftopt.time_grid import DAYS_PER_WEEK

WeekDay = Annotated[int, Field(ge=0, lt=DAYS_PER_WEEK)]


def _unique_days(days: list[int]) -> list[int]:
    if len(set(days)) != len(days):
        raise ValueError("request days must not repeat")
    return sorted(days)


class EmployeeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=120)
    hourly_wage: int = Field(gt=0)
    unavailable_days: list[WeekDay] = Field(default_factory=list, max_length=DAYS_PER_WEEK)
    preferred_days_off: list[WeekDay] = Field(default_factory=list, max_length=DAYS_PER_WEEK)

    @field_validator("unavailable_days", "preferred_days_off")
    @classmethod
    def check_days(cls, value: list[int]) -> list[int]:
        return _unique_days(value)


class EmployeeUpdate(EmployeeCreate):
    pass


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    hourly_wage: int
    unavailable_days: list[int]
    preferred_days_off: list[int]
    created_at: datetime
