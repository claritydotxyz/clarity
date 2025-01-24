from datetime import datetime, timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from clarity.api.deps import get_current_user
from clarity.core.security import get_password_hash, verify_password
from clarity.models.user import User
from clarity.schemas.auth import Token, TokenPayload, UserCreate, UserLogin
from clarity.config.settings import settings
from clarity.core.database import get_async_session
import structlog

logger = structlog.get_logger()

router = APIRouter()

@router.post("/register", response_model=Token)
async def register_user(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_async_session)
) -> Any:
    """Register a new user."""
    # Check if user exists
    existing_user = await User.get_by_email(session, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Create new user
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session)
) -> Any:
    """OAuth2 compatible token login."""
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )

    # Log successful login
    logger.info(
        "auth.login.success",
        user_id=user.id,
        email=user.email,
        ip_address=request.client.host
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Logout current user."""
    # Implement token blacklisting or session invalidation here
    return {"msg": "Successfully logged out"}
