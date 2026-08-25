from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    short_name: str | None = Field(default=None, max_length=255)
    nature: str | None = Field(default=None, max_length=64)
    size: str | None = Field(default=None, max_length=64)
    industry: str | None = Field(default=None, max_length=128)
    headquarters_city: str | None = Field(default=None, max_length=128)
    business_description: str | None = None
    founded_date: date | None = None
    registered_capital: str | None = Field(default=None, max_length=128)
    official_website: str | None = Field(default=None, max_length=2048)

    model_config = {"extra": "forbid"}


class CompanyRead(BaseModel):
    id: UUID
    full_name: str

    model_config = {"from_attributes": True}
