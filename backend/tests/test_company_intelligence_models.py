import importlib.util
from pathlib import Path

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, create_engine, inspect


def test_verification_status_exposes_the_four_candidate_states() -> None:
    """Protects against a candidate result losing a required trust state."""
    from app.models.enums import VerificationStatus

    assert {status.value for status in VerificationStatus} == {
        "unverified",
        "candidate",
        "verified",
        "rejected",
    }


def test_recruitment_link_persists_validation_and_source_provenance() -> None:
    """Protects against confirmed links losing verification evidence."""
    from app.models.company import RecruitmentLink
    from app.models.enums import VerificationStatus

    columns = RecruitmentLink.__table__.c

    assert columns["verification_status"].default.arg is VerificationStatus.UNVERIFIED
    assert columns["verification_status"].type.enums == [
        "unverified",
        "candidate",
        "verified",
        "rejected",
    ]
    assert isinstance(columns["http_status"].type, Integer)
    assert isinstance(columns["final_url"].type, String)
    assert isinstance(columns["source_url"].type, String)
    assert isinstance(columns["source_title"].type, String)
    assert isinstance(columns["source_type"].type, String)
    assert isinstance(columns["retrieved_at"].type, DateTime)
    assert columns["retrieved_at"].type.timezone is True


def test_company_intelligence_settings_have_safe_non_secret_defaults() -> None:
    """Protects enrichment from a changed model, cache, or rate-limit policy."""
    from app.core.config import Settings

    settings = Settings(jwt_secret_key="test-only-jwt-secret-at-least-32-bytes")

    assert settings.kimi_model == "kimi-k2.5"
    assert settings.kimi_base_url == "https://api.moonshot.cn/v1"
    assert settings.kimi_web_search_formula == "moonshot/web-search:latest"
    assert settings.kimi_search_enabled is True
    assert settings.kimi_search_timeout_seconds == 8
    assert settings.company_intelligence_cache_ttl_seconds == 86_400
    assert settings.company_intelligence_rate_limit_max_requests == 10
    assert settings.company_intelligence_rate_limit_window_seconds == 60


def test_company_intelligence_migration_upgrades_and_downgrades_legacy_schema() -> None:
    """Protects a Phase 4 recruitment_links table from one-way migration failures."""
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "20260825_0003_company_intelligence.py"
    )
    spec = importlib.util.spec_from_file_location("company_intelligence_migration", migration_path)
    assert spec is not None
    assert spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    metadata = MetaData()
    Table(
        "recruitment_links",
        metadata,
        Column("id", Integer, primary_key=True),
    )
    metadata.create_all(engine)

    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            migration.upgrade()

        column_names = {
            column["name"] for column in inspect(connection).get_columns("recruitment_links")
        }
        assert column_names == {
            "id",
            "verification_status",
            "http_status",
            "final_url",
            "source_url",
            "source_title",
            "source_type",
            "retrieved_at",
        }

        with Operations.context(context):
            migration.downgrade()

        column_names = {
            column["name"] for column in inspect(connection).get_columns("recruitment_links")
        }
        assert column_names == {"id"}


def test_sync_import_migration_handles_a_column_created_by_the_initial_schema() -> None:
    """Protect a fresh schema from failing when Phase 6 adds its already-present column."""
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "20260826_0004_phase6_sync_import.py"
    )
    spec = importlib.util.spec_from_file_location("sync_import_migration", migration_path)
    assert spec is not None
    assert spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    metadata = MetaData()
    Table(
        "job_applications",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, nullable=False),
        Column("client_sync_id", String, nullable=True),
    )
    metadata.create_all(engine)

    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            migration.upgrade()

        index_names = {
            index["name"] for index in inspect(connection).get_indexes("job_applications")
        }
        assert index_names == {"uq_job_applications_user_client_sync_id"}
