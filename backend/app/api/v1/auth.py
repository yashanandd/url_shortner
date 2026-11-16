from fastapi import APIRouter, Depends, HTTPException, Request, status
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.models.user import User
from app.schemas.user import (
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.rate_limiter import is_rate_limited
from app.services.user_service import (
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
    authenticate_user,
    refresh_access_token,
    register_user,
    revoke_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Register a new LinkFlow account."""
    client_ip = request.client.host if request.client else "unknown"
    limited, retry_after = await is_rate_limited(
        redis=redis,
        key_identifier=f"auth:register:{client_ip}",
        limit=settings.RATE_LIMIT_AUTH_PER_MIN,
        window_seconds=60,
    )
    if limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many registration attempts. Please retry in {retry_after} seconds.",
        )

    try:
        user = await register_user(db, data)
        return user
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Authenticate and receive access and refresh tokens."""
    client_ip = request.client.host if request.client else "unknown"
    limited, retry_after = await is_rate_limited(
        redis=redis,
        key_identifier=f"auth:login:{client_ip}",
        limit=settings.RATE_LIMIT_AUTH_PER_MIN,
        window_seconds=60,
    )
    if limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please retry in {retry_after} seconds.",
        )

    try:
        return await authenticate_user(db, redis, data)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Rotate and refresh an access token using a valid refresh token."""
    try:
        return await refresh_access_token(db, redis, data.refresh_token)
    except InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    data: RefreshTokenRequest,
    redis: aioredis.Redis = Depends(get_redis),
):
    """Revoke a refresh token on logout."""
    await revoke_refresh_token(redis, data.refresh_token)
    return {"message": "Successfully logged out."}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Get profile details of the logged-in user."""
    return current_user
