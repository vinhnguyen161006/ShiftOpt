from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EmployeeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=120)
    hourly_wage: int = Field(gt=0)


class EmployeeUpdate(EmployeeCreate):
    pass


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    hourly_wage: int
    created_at: datetime
