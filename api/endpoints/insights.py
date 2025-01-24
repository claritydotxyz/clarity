from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from clarity.api.deps import get_current_user
from clarity.core.engine.analyzer import InsightAnalyzer
from clarity.models.user import User
from clarity.models.insight import Insight
from clarity.schemas.insight import InsightCreate, InsightResponse
from clarity.core.database import get_async_session

router = APIRouter()

@router.get("/", response_model=List[InsightResponse])
async def get_insights(
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    category: str = Query(None),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Any:
    """Get insights for the current user."""
    insights = await Insight.get_multi_by_user(
        session=session,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        category=category,
        limit=limit
    )
    
    return insights

@router.get("/summary", response_model=InsightSummary)
async def get_insight_summary(
    timeframe: str = Query("week", regex="^(day|week|month|year)$"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Any:
    """Get summarized insights for the specified timeframe."""
    analyzer = InsightAnalyzer()
    summary = await analyzer.generate_summary(
        user_id=current_user.id,
        timeframe=timeframe,
        session=session
    )
    return summary

@router.get("/recommendations", response_model=List[RecommendationResponse])
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Any:
    """Get personalized recommendations based on insights."""
    analyzer = InsightAnalyzer()
    recommendations = await analyzer.generate_recommendations(
        user_id=current_user.id,
        session=session
    )
    return recommendations
