from typing import List
from pydantic import PostgresDsn, RedisDsn, SecretStr
from clarity.config.base import BaseSettings

class ProductionSettings(BaseSettings):
    # Application
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Database
    POSTGRES_SERVER: str = "db.production"
    POSTGRES_USER: str = "clarity_prod"
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str = "clarity_prod"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    # Redis
    REDIS_HOST: str = "redis.production"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: SecretStr
    
    # Security
    SECRET_KEY: SecretStr
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["https://claritys.xyz"]
    
    # Monitoring
    SENTRY_DSN: str
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp"
    LOG_LEVEL: str = "INFO"
    
    # SSL/TLS
    SSL_KEYFILE: str = "/etc/ssl/private/clarity.key"
    SSL_CERTFILE: str = "/etc/ssl/certs/clarity.crt"
    
    # Feature flags
    ENABLE_ML_FEATURES: bool = True
    ENABLE_PROFILING: bool = False
    
    class Config:
        case_sensitive = True
        env_file = ".env"
