from typing import Any

from fastapi.responses import JSONResponse

from app.core.errors import AppError


def success_response(data: Any = None, message: str = "success", status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": 0, "message": message, "data": data},
    )


def error_response(error: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"code": int(error.code), "message": error.message, "data": None},
    )
