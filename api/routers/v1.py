from fastapi import APIRouter, Depends, HTTPException
from api.endpoints import auth, insights, patterns, users
from api.middleware.auth import get_current_user

router = APIRouter()

router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

router.include_router(
    insights.router,
    prefix="/insights",
    tags=["insights"],
    dependencies=[Depends(get_current_user)]
)

router.include_router(
    patterns.router,
    prefix="/patterns",
    tags=["patterns"],
    dependencies=[Depends(get_current_user)]
)

router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)
