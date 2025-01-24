from datetime import datetime
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from clarity.core.database import get_async_session
from clarity.core.security import verify_password
from clarity.models.user import User
from clarity.schemas.token import TokenPayload
from clarity.config.settings import settings
import structlog

logger = structlog.get_logger()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_current_user(
    session: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get the current authenticated user based on the JWT token.
    
    Args:
        session: Database session
        token: JWT token from request
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError as e:
        logger.error("auth.token.invalid", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user = await session.get(User, token_data.sub)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
            
        # Update last activity
        user.last_active = datetime.utcnow()
        session.add(user)
        await session.commit()
        
        return user
        
    except Exception as e:
        logger.error("auth.user.fetch_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Check if current user is superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

# Rate limiting dependency
async def check_rate_limit(
    user: User = Depends(get_current_user),
) -> None:
    """
    Check rate limiting for current user.
    Implements a sliding window rate limit.
    """
    # Implementation details would go here
    pass

# API Key authentication for external services
async def verify_api_key(
    api_key: str,
    session: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    """Verify API key for external service authentication."""
    # Implementation details would go here
    pass
