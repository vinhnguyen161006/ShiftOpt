from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.time_grid import DAYS_PER_WEEK

WeekDay = Annotated[int, Field(ge=0, lt=DAYS_PER_WEEK)]
WeeklyHours = Annotated[int, Field(ge=1, le=LaborRules().max_weekly_hours)]


def _unique_days(days: list[int]) -> list[int]:
    if len(set(days)) != len(days):
        raise ValueError("request days must not repeat")
    return sorted(days)


class EmployeeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=120)
    hourly_wage: int = Field(gt=0)
    max_weekly_hours: WeeklyHours | None = None
    min_weekly_hours: WeeklyHours | None = None
    unavailable_days: list[WeekDay] = Field(default_factory=list, max_length=DAYS_PER_WEEK)
    preferred_days_off: list[WeekDay] = Field(default_factory=list, max_length=DAYS_PER_WEEK)

    @field_validator("unavailable_days", "preferred_days_off")
    @classmethod
    def check_days(cls, value: list[int]) -> list[int]:
        return _unique_days(value)

    @model_validator(mode="after")
    def check_minimum_not_above_maximum(self) -> "EmployeeCreate":
        if (
            self.min_weekly_hours is not None
            and self.max_weekly_hours is not None
            and self.min_weekly_hours > self.max_weekly_hours
        ):
            raise ValueError("min_weekly_hours must not exceed max_weekly_hours")
        return self


class EmployeeUpdate(EmployeeCreate):
    pass


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    hourly_wage: int
    max_weekly_hours: int | None
    min_weekly_hours: int | None
    unavailable_days: list[int]
    preferred_days_off: list[int]
    created_at: datetime
