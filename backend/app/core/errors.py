from enum import IntEnum


class ErrorCode(IntEnum):
    AUTH_REQUIRED = 10001
    TOKEN_EXPIRED = 10002
    PERMISSION_DENIED = 10003
    INVALID_CREDENTIALS = 10004
    USER_ALREADY_EXISTS = 10005
    COMPANY_NOT_FOUND = 20001
    COMPANY_AMBIGUOUS = 20002
    COMPANY_FETCH_TIMEOUT = 20003
    COMPANY_PROVIDER_ERROR = 20004
    LINK_INVALID = 30001
    LINK_CHECK_TIMEOUT = 30002
    LINK_DISCOVERY_FAILED = 30003
    APPLICATION_NOT_FOUND = 40001
    APPLICATION_DUPLICATE = 40002
    APPLICATION_CREATE_FAILED = 40003
    STATUS_INVALID = 40004
    RATE_LIMITED = 50002
    DATABASE_ERROR = 50003
    SERVICE_UNAVAILABLE = 50001
    INTERNAL_ERROR = 50000


class AppError(Exception):
    def __init__(self, code: ErrorCode, message: str, status_code: int | None = None) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code or _default_status(code)
        super().__init__(message)


def _default_status(code: ErrorCode) -> int:
    if code in {ErrorCode.AUTH_REQUIRED, ErrorCode.TOKEN_EXPIRED}:
        return 401
    if code is ErrorCode.INVALID_CREDENTIALS:
        return 401
    if code is ErrorCode.USER_ALREADY_EXISTS:
        return 409
    if code is ErrorCode.PERMISSION_DENIED:
        return 403
    if code is ErrorCode.SERVICE_UNAVAILABLE:
        return 503
    if code is ErrorCode.INTERNAL_ERROR:
        return 500
    return 400
