from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from clarity.core.patterns.behavior import BehaviorAnalyzer
from clarity.core.patterns.financial import FinancialAnalyzer
from clarity.core.patterns.temporal import TemporalAnalyzer
from clarity.api.deps import get_current_user, get_async_session
from clarity.schemas.patterns import PatternResponse
from clarity.models.user import User
import structlog

logger = structlog.get_logger()

router = APIRouter()

@router.get("/behavior", response_model=List[PatternResponse])
async def get_behavior_patterns(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get behavior patterns for the current user."""
    try:
        analyzer = BehaviorAnalyzer()
        behavior_data = await analyzer.get_user_data(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            session=session
        )
        patterns = await analyzer.analyze(behavior_data)
        
        return [PatternResponse(**pattern.dict()) for pattern in patterns]
        
    except Exception as e:
        logger.error(
            "patterns.behavior_failed",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze behavior patterns"
        )

@router.get("/financial", response_model=List[PatternResponse])
async def get_financial_patterns(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get financial patterns for the current user."""
    try:
        analyzer = FinancialAnalyzer()
        financial_data = await analyzer.get_user_data(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            session=session
        )
        patterns = await analyzer.analyze(financial_data)
        
        return [PatternResponse(**pattern.dict()) for pattern in patterns]
        
    except Exception as e:
        logger.error(
            "patterns.financial_failed",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze financial patterns"
        )

@router.get("/temporal", response_model=List[PatternResponse])
async def get_temporal_patterns(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get temporal patterns for the current user."""
    try:
        analyzer = TemporalAnalyzer()
        temporal_data = await analyzer.get_user_data(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            session=session
        )
        patterns = await analyzer.analyze(temporal_data)
        
        return [PatternResponse(**pattern.dict()) for pattern in patterns]
        
    except Exception as e:
        logger.error(
            "patterns.temporal_failed",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze temporal patterns"
        )
