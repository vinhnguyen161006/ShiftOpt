from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShiftTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    start_hour: int = Field(ge=0, le=23)
    length_hours: int = Field(8, ge=1, le=24)


class ShiftTemplateUpdate(ShiftTemplateCreate):
    pass


class ShiftTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_hour: int
    length_hours: int
    created_at: datetime
