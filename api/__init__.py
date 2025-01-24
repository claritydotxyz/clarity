"""
Clarity API Package

This package contains all API-related functionality including endpoints,
middleware, and routing logic for the Clarity application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from clarity.config.settings import settings

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="AI Resource Compass - Personal efficiency dashboard",
        version=settings.VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
