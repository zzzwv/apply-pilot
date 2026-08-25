from app.core.errors import AppError, ErrorCode
from app.core.responses import error_response, success_response


def test_success_response_uses_the_standard_envelope() -> None:
    """Catches an API response that omits code=0 or changes its payload shape."""
    response = success_response({"item": "application"})

    assert response.status_code == 200
    assert response.body == b'{"code":0,"message":"success","data":{"item":"application"}}'


def test_error_response_maps_an_application_error_to_its_api_code() -> None:
    """Catches application errors leaking HTTP status or losing their error code."""
    response = error_response(AppError(ErrorCode.AUTH_REQUIRED, "Authentication required"))

    assert response.status_code == 401
    assert response.body == b'{"code":10001,"message":"Authentication required","data":null}'
