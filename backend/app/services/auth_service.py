from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.schemas.auth import AuthResponse, LoginRequest
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_service = UserService(db)

    async def register_user(self, payload: UserCreate) -> AuthResponse:
        existing_user = await self.user_service.get_by_email(payload.email)
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

        user = await self.user_service.create(payload)
        access_token = create_access_token(str(user.id), {"email": user.email})

        return AuthResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserRead.model_validate(user),
        )

    async def authenticate_user(self, payload: LoginRequest) -> AuthResponse:
        user = await self.user_service.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        access_token = create_access_token(str(user.id), {"email": user.email})
        return AuthResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserRead.model_validate(user),
        )
