from fastapi import APIRouter
from clarity.api.endpoints import insights, patterns
from clarity.config.settings import settings

router = APIRouter(prefix=settings.API_V2_STR)

# Include updated endpoints for v2 API
router.include_router(
    insights.router_v2,
    prefix="/insights",
    tags=["insights"]
)

router.include_router(
    patterns.router_v2,
    prefix="/patterns",
    tags=["patterns"]
)
