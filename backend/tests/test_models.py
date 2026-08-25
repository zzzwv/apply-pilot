from sqlalchemy import Index


def test_phase_one_metadata_contains_the_six_required_tables_and_indexes() -> None:
    """Catches missing Phase 1 entities or the user-scoped query indexes from the TDD."""
    from app.models import Base

    tables = Base.metadata.tables

    assert set(tables) == {
        "users",
        "companies",
        "company_aliases",
        "recruitment_links",
        "job_applications",
        "application_status_logs",
    }
    application_indexes = {index.name for index in tables["job_applications"].indexes}
    assert {
        "ix_job_applications_user_id",
        "ix_job_applications_company_id",
        "ix_job_applications_current_status",
        "ix_job_applications_application_type",
        "ix_job_applications_application_date",
        "ix_job_applications_user_application_date",
        "ix_job_applications_user_current_status",
        "ix_job_applications_user_application_type",
    } <= application_indexes


def test_application_status_enum_matches_the_prd() -> None:
    """Catches a missing or renamed workflow status before it reaches a migration."""
    from app.models.enums import ApplicationStatus

    assert [status.value for status in ApplicationStatus] == [
        "NOT_APPLIED",
        "APPLIED",
        "RESUME_PASSED",
        "FIRST_INTERVIEW",
        "SECOND_INTERVIEW",
        "FINAL_INTERVIEW",
        "HR_INTERVIEW",
        "SALARY_NEGOTIATION",
        "OFFER_RECEIVED",
        "OFFER_REJECTED",
        "RESUME_REJECTED",
        "INTERVIEW_REJECTED",
        "PROCESS_TERMINATED",
        "SIGNED",
    ]


def test_status_log_is_bound_to_both_application_and_user() -> None:
    """Catches status logs that cannot be checked against the owning user."""
    from app.models import Base

    foreign_keys = {foreign_key.target_fullname for foreign_key in Base.metadata.tables["application_status_logs"].foreign_keys}

    assert "job_applications.id" in foreign_keys
    assert "users.id" in foreign_keys
