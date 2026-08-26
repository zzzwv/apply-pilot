from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import ApplicationStatus, ApplicationType


class ApplicationSort(str, Enum):
    APPLICATION_DATE_ASC = "application_date_asc"
    APPLICATION_DATE_DESC = "application_date_desc"
    COMPANY_NAME_ASC = "company_name_asc"
    STATUS_PRIORITY_DESC = "status_priority_desc"


class ApplicationFilterParams(BaseModel):
    keyword: str | None = None
    statuses: list[ApplicationStatus] = []
    company_natures: list[str] = []
    application_types: list[ApplicationType] = []
    industries: list[str] = []
    date_from: date | None = None
    date_to: date | None = None
    company_sizes: list[str] = []
    sort: ApplicationSort = ApplicationSort.APPLICATION_DATE_DESC
    page: int = 1
    page_size: int = 20


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


class ApplicationCompanyRead(BaseModel):
    id: UUID
    full_name: str
    short_name: str | None
    industry: str | None
    nature: str | None
    size: str | None

    model_config = {"from_attributes": True}


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
    company: ApplicationCompanyRead

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


class SyncCompany(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    short_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=128)
    nature: str | None = Field(default=None, max_length=64)
    size: str | None = Field(default=None, max_length=64)

    model_config = {"extra": "forbid"}


class SyncStatusLog(BaseModel):
    from_status: ApplicationStatus | None = None
    to_status: ApplicationStatus
    remark: str | None = None
    changed_at: datetime

    model_config = {"extra": "forbid"}


class SyncImportApplication(BaseModel):
    client_sync_id: UUID
    company: SyncCompany
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
    status_logs: list[SyncStatusLog] = Field(min_length=1, max_length=100)

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_status_history(self) -> "SyncImportApplication":
        previous_status: ApplicationStatus | None = None
        for status_log in self.status_logs:
            if status_log.from_status != previous_status:
                raise ValueError("status_logs must form a continuous status chain")
            previous_status = status_log.to_status
        if previous_status != self.current_status:
            raise ValueError("status_logs must end at current_status")
        return self


class SyncImportRequest(BaseModel):
    applications: list[SyncImportApplication] = Field(min_length=1, max_length=200)

    model_config = {"extra": "forbid"}
