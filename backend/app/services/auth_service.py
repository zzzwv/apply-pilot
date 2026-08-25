from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, UserCreate


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def register(self, payload: UserCreate) -> User:
        if await self.users.get_by_username_or_email(payload.username) or await self.users.get_by_username_or_email(payload.email):
            raise AppError(ErrorCode.USER_ALREADY_EXISTS, "Username or email already exists")
        user = self.users.add(User(username=payload.username, email=payload.email, password_hash=hash_password(payload.password)))
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def login(self, payload: LoginRequest) -> str:
        user = await self.users.get_by_username_or_email(payload.username_or_email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise AppError(ErrorCode.INVALID_CREDENTIALS, "Invalid username/email or password")
        return create_access_token(str(user.id))
