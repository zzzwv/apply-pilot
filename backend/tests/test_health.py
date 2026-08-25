from collections.abc import Awaitable, Callable

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_uniform_success_after_dependencies_are_healthy() -> None:
    """Catches a health endpoint that reports ready before all dependencies are checked."""
    async def healthy() -> None:
        return None

    client = TestClient(create_app(health_check=healthy))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"code": 0, "message": "success", "data": {"status": "ok"}}
    assert response.headers["x-request-id"]


def test_health_returns_uniform_service_unavailable_when_a_dependency_fails() -> None:
    """Catches an unavailable dependency being exposed as an unstructured server failure."""
    async def unavailable() -> None:
        raise ConnectionError("redis unavailable")

    client = TestClient(create_app(health_check=unavailable))

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "code": 50001,
        "message": "Service unavailable",
        "data": None,
    }
