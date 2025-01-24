from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from clarity.api.deps import get_current_user, get_current_active_superuser
from clarity.models.user import User
from clarity.schemas.user import UserCreate, UserUpdate, UserResponse
from clarity.core.security import get_password_hash
import structlog

logger = structlog.get_logger()

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return UserResponse.from_orm(current_user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update current user information."""
    try:
        update_data = user_update.dict(exclude_unset=True)
        
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            
        for field, value in update_data.items():
            setattr(current_user, field, value)
            
        session.add(current_user)
        await session.commit()
        await session.refresh(current_user)
        
        return UserResponse.from_orm(current_user)
        
    except Exception as e:
        logger.error(
            "users.update_failed",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to update user"
        )

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all users (superuser only)."""
    try:
        users = await User.get_multi(session, skip=skip, limit=limit)
        return [UserResponse.from_orm(user) for user in users]
        
    except Exception as e:
        logger.error("users.fetch_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch users"
        )
