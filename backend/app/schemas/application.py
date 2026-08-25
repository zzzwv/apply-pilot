from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import ApplicationStatus, ApplicationType


class ApplicationCreate(BaseModel):
    company_id: UUID
    job_title: str = Field(min_length=1, max_length=255)
    application_type: ApplicationType
    application_date: date
    channel: str = Field(min_length=1, max_length=128)
    resume_version: str | None = Field(default=None, max_length=128)
    salary: str | None = Field(default=None, max_length=128)
    city: str | None = Field(default=None, max_length=128)
    education_requirement: str | None = Field(default=None, max_length=128)
    deadline: date | None = None
    requirements: str | None = None
    note: str | None = None
    current_status: ApplicationStatus = ApplicationStatus.NOT_APPLIED

    model_config = {"extra": "forbid"}


class ApplicationUpdate(BaseModel):
    company_id: UUID | None = None
    job_title: str | None = Field(default=None, min_length=1, max_length=255)
    application_type: ApplicationType | None = None
    application_date: date | None = None
    channel: str | None = Field(default=None, min_length=1, max_length=128)
    resume_version: str | None = Field(default=None, max_length=128)
    salary: str | None = Field(default=None, max_length=128)
    city: str | None = Field(default=None, max_length=128)
    education_requirement: str | None = Field(default=None, max_length=128)
    deadline: date | None = None
    requirements: str | None = None
    note: str | None = None

    model_config = {"extra": "forbid"}


class ApplicationRead(BaseModel):
    id: UUID
    user_id: UUID
    company_id: UUID
    job_title: str
    application_type: ApplicationType
    application_date: date
    channel: str
    resume_version: str | None
    salary: str | None
    city: str | None
    education_requirement: str | None
    deadline: date | None
    requirements: str | None
    note: str | None
    current_status: ApplicationStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationListResponse(BaseModel):
    items: list[ApplicationRead]
    total: int
    page: int
    page_size: int


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    remark: str | None = None

    model_config = {"extra": "forbid"}


class ApplicationStatusLogRead(BaseModel):
    id: UUID
    application_id: UUID
    from_status: ApplicationStatus | None
    to_status: ApplicationStatus
    remark: str | None
    changed_at: datetime

    model_config = {"from_attributes": True}


class ApplicationStatusLogListResponse(BaseModel):
    items: list[ApplicationStatusLogRead]


class ApplicationBatchDeleteRequest(BaseModel):
    ids: list[UUID] = Field(min_length=1, max_length=1000)

    model_config = {"extra": "forbid"}


class DeletedCountResponse(BaseModel):
    deleted_count: int
