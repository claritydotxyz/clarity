from typing import List
from pydantic import PostgresDsn, RedisDsn, SecretStr
from clarity.config.base import BaseSettings

class DevelopmentSettings(BaseSettings):
    # Application
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "clarity_dev"
    POSTGRES_PASSWORD: SecretStr = SecretStr("claritydefaultpassword123")
    POSTGRES_DB: str = "clarity_dev"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: SecretStr = SecretStr("")
    
    # Security
    SECRET_KEY: SecretStr = SecretStr("")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Logging
    LOG_LEVEL: str = "DEBUG"
    
    # Feature flags
    ENABLE_ML_FEATURES: bool = True
    ENABLE_PROFILING: bool = True
    
    class Config:
        case_sensitive = True
