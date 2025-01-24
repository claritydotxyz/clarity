from functools import lru_cache
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseSettings, PostgresDsn, RedisDsn, SecretStr, EmailStr, validator
import structlog

logger = structlog.get_logger()

class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "Clarity"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    API_V2_STR: str = "/api/v2"
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Authentication
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD").get_secret_value(),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # Redis
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: SecretStr
    REDIS_URI: Optional[RedisDsn] = None
    
    @validator("REDIS_URI", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return RedisDsn.build(
            scheme="redis",
            host=values.get("REDIS_HOST"),
            port=str(values.get("REDIS_PORT")),
            password=values.get("REDIS_PASSWORD").get_secret_value(),
        )
    
    # Email
    SMTP_TLS: bool = True
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: SecretStr
    EMAILS_FROM_EMAIL: EmailStr
    EMAILS_FROM_NAME: str
    
    # ML Model Settings
    MODEL_PATH: str = "models"
    MODEL_UPDATE_FREQUENCY: int = 24  # hours
    FEATURE_STORE_PATH: str = "data/features"
    
    # Integration Settings
    PLAID_CLIENT_ID: SecretStr
    PLAID_SECRET: SecretStr
    PLAID_ENV: str = "development"
    
    STRIPE_SECRET_KEY: SecretStr
    STRIPE_WEBHOOK_SECRET: SecretStr
    
    GITHUB_TOKEN: SecretStr
    GITLAB_TOKEN: SecretStr
    JIRA_TOKEN: SecretStr
    SLACK_BOT_TOKEN: SecretStr
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp"
    LOG_LEVEL: str = "INFO"
    
    # Performance
    PERFORMANCE_PROFILING: bool = False
    TRACE_SAMPLING_RATE: float = 0.1
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    try:
        settings = Settings()
        logger.info("settings.loaded", 
                   project_name=settings.PROJECT_NAME,
                   version=settings.VERSION,
                   environment="production" if settings.SENTRY_DSN else "development")
        return settings
    except Exception as e:
        logger.error("settings.load_failed", error=str(e))
        raise

settings = get_settings()
