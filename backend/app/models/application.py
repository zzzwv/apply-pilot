import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, utc_now
from app.models.enums import ApplicationStatus, ApplicationType


class JobApplication(TimestampMixin, Base):
    __tablename__ = "job_applications"
    __table_args__ = (
        Index("ix_job_applications_user_application_date", "user_id", "application_date"),
        Index("ix_job_applications_user_current_status", "user_id", "current_status"),
        Index("ix_job_applications_user_application_type", "user_id", "application_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), index=True, nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    application_type: Mapped[ApplicationType] = mapped_column(index=True, nullable=False)
    application_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(128), nullable=False)
    resume_version: Mapped[str | None] = mapped_column(String(128))
    salary: Mapped[str | None] = mapped_column(String(128))
    city: Mapped[str | None] = mapped_column(String(128))
    education_requirement: Mapped[str | None] = mapped_column(String(128))
    deadline: Mapped[date | None] = mapped_column(Date)
    requirements: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    client_sync_id: Mapped[uuid.UUID | None] = mapped_column(index=True, nullable=True)
    current_status: Mapped[ApplicationStatus] = mapped_column(index=True, default=ApplicationStatus.NOT_APPLIED, nullable=False)

    user: Mapped["User"] = relationship(back_populates="applications")
    company: Mapped["Company"] = relationship(back_populates="applications")
    status_logs: Mapped[list["ApplicationStatusLog"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class ApplicationStatusLog(Base):
    __tablename__ = "application_status_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_applications.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    from_status: Mapped[ApplicationStatus | None] = mapped_column()
    to_status: Mapped[ApplicationStatus] = mapped_column(nullable=False)
    remark: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    application: Mapped[JobApplication] = relationship(back_populates="status_logs")
    user: Mapped["User"] = relationship(back_populates="status_logs")
