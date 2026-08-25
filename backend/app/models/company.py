import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, utc_now
from app.models.enums import LinkStatus, RecruitmentChannel, RecruitmentLinkType, VerificationStatus


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(255))
    nature: Mapped[str | None] = mapped_column(String(64))
    size: Mapped[str | None] = mapped_column(String(64))
    industry: Mapped[str | None] = mapped_column(String(128))
    headquarters_city: Mapped[str | None] = mapped_column(String(128))
    business_description: Mapped[str | None] = mapped_column(Text)
    founded_date: Mapped[date | None] = mapped_column(Date)
    registered_capital: Mapped[str | None] = mapped_column(String(128))
    official_website: Mapped[str | None] = mapped_column(String(2048))

    aliases: Mapped[list["CompanyAlias"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    recruitment_links: Mapped[list["RecruitmentLink"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    applications: Mapped[list["JobApplication"]] = relationship(back_populates="company")


class CompanyAlias(Base):
    __tablename__ = "company_aliases"
    __table_args__ = (UniqueConstraint("company_id", "normalized_alias", name="uq_company_aliases_company_normalized"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    company: Mapped[Company] = relationship(back_populates="aliases")


class RecruitmentLink(TimestampMixin, Base):
    __tablename__ = "recruitment_links"
    __table_args__ = (UniqueConstraint("company_id", "url", name="uq_recruitment_links_company_url"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    channel: Mapped[RecruitmentChannel] = mapped_column(nullable=False)
    link_type: Mapped[RecruitmentLinkType] = mapped_column(nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_status: Mapped[LinkStatus] = mapped_column(default=LinkStatus.UNKNOWN, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str | None] = mapped_column(String(128))
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SqlEnum(
            VerificationStatus,
            values_callable=lambda statuses: [status.value for status in statuses],
            name="verificationstatus",
        ),
        default=VerificationStatus.UNVERIFIED, nullable=False
    )
    http_status: Mapped[int | None] = mapped_column(Integer)
    final_url: Mapped[str | None] = mapped_column(String(2048))
    source_url: Mapped[str | None] = mapped_column(String(2048))
    source_title: Mapped[str | None] = mapped_column(String(512))
    source_type: Mapped[str | None] = mapped_column(String(64))
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    company: Mapped[Company] = relationship(back_populates="recruitment_links")
