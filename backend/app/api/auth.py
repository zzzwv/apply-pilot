from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.errors import AppError, ErrorCode
from app.core.responses import success_response
from app.core.security import decode_access_token
from app.models import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)
SessionDependency = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: SessionDependency,
) -> User:
    if credentials is None:
        raise AppError(ErrorCode.AUTH_REQUIRED, "Authentication required")
    user = await UserRepository(session).get_by_id(decode_access_token(credentials.credentials))
    if user is None:
        raise AppError(ErrorCode.AUTH_REQUIRED, "Authentication required")
    return user


@router.post("/register")
async def register(payload: UserCreate, session: SessionDependency):
    user = await AuthService(session).register(payload)
    return success_response(UserResponse.model_validate(user).model_dump(mode="json"), status_code=201)


@router.post("/login")
async def login(payload: LoginRequest, session: SessionDependency):
    token = await AuthService(session).login(payload)
    return success_response(TokenResponse(access_token=token).model_dump())


@router.get("/me")
async def me(current_user: Annotated[User, Depends(get_current_user)]):
    return success_response(UserResponse.model_validate(current_user).model_dump(mode="json"))
