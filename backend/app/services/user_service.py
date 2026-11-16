import uuid
from datetime import datetime, timezone
from typing import Optional
import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import TokenResponse, UserLogin, UserRegister


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


REFRESH_TOKEN_PREFIX = "refresh_token:"


async def register_user(db: AsyncSession, register_data: UserRegister) -> User:
    """Register a new user with hashed password."""
    existing = await db.scalar(select(User).where(User.email == register_data.email.lower()))
    if existing:
        raise UserAlreadyExistsError("An account with this email already exists.")

    user = User(
        id=uuid.uuid4(),
        email=register_data.email.lower(),
        password_hash=hash_password(register_data.password),
        name=register_data.name,
        role="user",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    redis: aioredis.Redis,
    login_data: UserLogin,
) -> TokenResponse:
    """Validate credentials and issue access + refresh tokens."""
    user = await db.scalar(select(User).where(User.email == login_data.email.lower()))
    if not user or not verify_password(login_data.password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password.")

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Decode refresh token to get JTI and expiry for Redis tracking
    payload = decode_token(refresh_token)
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 60)
        await redis.setex(f"{REFRESH_TOKEN_PREFIX}{jti}", ttl, str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


async def refresh_access_token(
    db: AsyncSession,
    redis: aioredis.Redis,
    refresh_token: str,
) -> TokenResponse:
    """Validate refresh token against Redis and issue new access & refresh tokens."""
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise InvalidTokenError("Invalid or expired refresh token.")

    if payload.get("type") != "refresh":
        raise InvalidTokenError("Token is not a refresh token.")

    jti = payload.get("jti")
    user_id_str = payload.get("sub")
    if not jti or not user_id_str:
        raise InvalidTokenError("Invalid token payload.")

    # Check if refresh token is in Redis (revocation check)
    stored_user_id = await redis.get(f"{REFRESH_TOKEN_PREFIX}{jti}")
    if not stored_user_id or stored_user_id != user_id_str:
        raise InvalidTokenError("Refresh token has been revoked or expired.")

    # Revoke old refresh token (token rotation)
    await redis.delete(f"{REFRESH_TOKEN_PREFIX}{jti}")

    user = await db.scalar(select(User).where(User.id == uuid.UUID(user_id_str)))
    if not user:
        raise InvalidTokenError("User no longer exists.")

    new_token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    new_access_token = create_access_token(new_token_data)
    new_refresh_token = create_refresh_token(new_token_data)

    new_payload = decode_token(new_refresh_token)
    new_jti = new_payload.get("jti")
    new_exp = new_payload.get("exp")
    if new_jti and new_exp:
        ttl = max(int(new_exp - datetime.now(timezone.utc).timestamp()), 60)
        await redis.setex(f"{REFRESH_TOKEN_PREFIX}{new_jti}", ttl, str(user.id))

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


async def revoke_refresh_token(redis: aioredis.Redis, refresh_token: str) -> None:
    """Revoke a refresh token on user logout."""
    try:
        payload = decode_token(refresh_token)
        jti = payload.get("jti")
        if jti:
            await redis.delete(f"{REFRESH_TOKEN_PREFIX}{jti}")
    except Exception:
        pass
