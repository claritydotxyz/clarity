from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import v1, v2
from core.engine.collector import DataCollector
from utils.monitoring.logging import setup_logging

app = FastAPI(
    title="Clarity - AI Resource Compass",
    description="Personal efficiency dashboard that shows you exactly where your time and money are going",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
setup_logging()

# Include routers
app.include_router(v1.router, prefix="/api/v1")
app.include_router(v2.router, prefix="/api/v2")

# Initialize data collector
collector = DataCollector()

@app.on_event("startup")
async def startup_event():
    await collector.start()

@app.on_event("shutdown")
async def shutdown_event():
    await collector.stop()
