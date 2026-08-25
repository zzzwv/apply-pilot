from uuid import UUID

from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)

    model_config = {"extra": "forbid"}


class CompanyRead(BaseModel):
    id: UUID
    full_name: str

    model_config = {"from_attributes": True}
