from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_settings_accept_railway_standard_environment_variables(monkeypatch) -> None:
    """Catches Railway URLs being ignored because only project-prefixed names are accepted."""
    monkeypatch.delenv("JOB_TRACKER_JWT_SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@db.railway.internal:5432/railway")
    monkeypatch.setenv("REDIS_URL", "redis://default:password@redis.railway.internal:6379")
    monkeypatch.setenv("JWT_SECRET", "railway-jwt-secret-at-least-32-bytes")
    monkeypatch.setenv("FRONTEND_ORIGIN", "https://applypilot.vercel.app")

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql+asyncpg://user:password@db.railway.internal:5432/railway"
    assert settings.redis_url == "redis://default:password@redis.railway.internal:6379"
    assert settings.jwt_secret_key == "railway-jwt-secret-at-least-32-bytes"
    assert settings.cors_origins == ["https://applypilot.vercel.app"]


def test_app_allows_cors_preflight_from_configured_frontend_origin(monkeypatch) -> None:
    """Catches deployed browser requests being rejected despite a configured Vercel origin."""
    settings = Settings(
        _env_file=None,
        jwt_secret_key="test-only-jwt-secret-at-least-32-bytes",
        frontend_origins="https://applypilot.vercel.app",
    )
    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    client = TestClient(create_app(health_check=lambda: None))

    response = client.options(
        "/health",
        headers={
            "Origin": "https://applypilot.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://applypilot.vercel.app"


def test_settings_strip_whitespace_and_trailing_slashes_from_cors_origins() -> None:
    """Catches a Vercel origin rejected because a comma-separated value is not normalized."""
    settings = Settings(
        _env_file=None,
        jwt_secret_key="test-only-jwt-secret-at-least-32-bytes",
        frontend_origins="http://localhost:5173, https://applypilot.vercel.app/",
    )

    assert settings.cors_origins == ["http://localhost:5173", "https://applypilot.vercel.app"]
