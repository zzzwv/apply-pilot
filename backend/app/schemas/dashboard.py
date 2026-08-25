from datetime import date
from enum import Enum

from pydantic import BaseModel

from app.models.enums import ApplicationStatus


class TrendGranularity(str, Enum):
    DAY = "day"
    WEEK = "week"


class DashboardSummaryRead(BaseModel):
    total: int
    in_progress: int
    offer_count: int
    interview_rate: float
    offer_rate: float
    rejection_rate: float


class StatusDistributionItem(BaseModel):
    status: ApplicationStatus
    count: int
    percentage: float


class IndustryDistributionItem(BaseModel):
    industry: str
    count: int
    percentage: float


class CompanyNatureDistributionItem(BaseModel):
    company_nature: str
    count: int
    percentage: float


class StatusDistributionRead(BaseModel):
    items: list[StatusDistributionItem]


class IndustryDistributionRead(BaseModel):
    items: list[IndustryDistributionItem]


class CompanyNatureDistributionRead(BaseModel):
    items: list[CompanyNatureDistributionItem]


class TrendPoint(BaseModel):
    date: date
    count: int


class DashboardTrendRead(BaseModel):
    items: list[TrendPoint]
