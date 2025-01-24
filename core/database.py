from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from clarity.config.settings import settings
import structlog

logger = structlog.get_logger()

# Create SQLAlchemy models from this base class
Base = declarative_base()

# Create async engine for PostgreSQL
async_engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

# Create sync engine for background tasks
sync_engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("database.session.error", error=str(e))
            raise
        finally:
            await session.close()

def get_sync_session() -> Generator[AsyncSession, None, None]:
    """Dependency for getting sync database sessions."""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("database.sync_session.error", error=str(e))
        raise
    finally:
        session.close()

# Database health check
async def check_database_health() -> bool:
    """Check if the database is responsive."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error("database.health_check.failed", error=str(e))
        return False

# Connection pool monitoring
async def get_pool_status() -> dict:
    """Get database connection pool statistics."""
    return {
        "pool_size": async_engine.pool.size(),
        "checkedin": async_engine.pool.checkedin(),
        "checkedout": async_engine.pool.checkedout(),
        "overflow": async_engine.pool.overflow(),
    }
