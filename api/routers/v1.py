from fastapi import APIRouter
from clarity.api.endpoints import auth, insights, patterns, users
from clarity.config.settings import settings

router = APIRouter(prefix=settings.API_V1_STR)

# Include endpoint routers with versioned prefix
router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

router.include_router(
    insights.router,
    prefix="/insights",
    tags=["insights"]
)

router.include_router(
    patterns.router,
    prefix="/patterns",
    tags=["patterns"]
)

router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)
