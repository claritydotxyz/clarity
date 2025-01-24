from typing import List
from pydantic import PostgresDsn, RedisDsn, SecretStr
from clarity.config.base import BaseSettings

class TestingSettings(BaseSettings):
    # Application
    DEBUG: bool = True
    ENVIRONMENT: str = "testing"
    TESTING: bool = True
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "clarity_test"
    POSTGRES_PASSWORD: SecretStr = SecretStr("test_password")
    POSTGRES_DB: str = "clarity_test"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: SecretStr = SecretStr("")
    
    # Security
    SECRET_KEY: SecretStr = SecretStr("test_secret_key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Logging
    LOG_LEVEL: str = "DEBUG"
    
    # Feature flags
    ENABLE_ML_FEATURES: bool = False
    ENABLE_PROFILING: bool = False
    
    class Config:
        case_sensitive = True

# File: docker/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.4.2

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application
COPY . .

# Create non-root user
RUN useradd -m clarity
USER clarity

# Run application
CMD ["poetry", "run", "uvicorn", "clarity.main:app", "--host", "0.0.0.0", "--port", "8000"]

# File: docker/docker-compose.yml
version: '3.8'

services:
  web:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - POSTGRES_SERVER=db
      - REDIS_HOST=redis
    depends_on:
      - db
      - redis
    volumes:
      - ../:/app
    networks:
      - clarity_network

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=clarity
      - POSTGRES_USER=clarity
      - POSTGRES_PASSWORD=clarity_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - clarity_network

  redis:
    image: redis:6
    command: redis-server --requirepass redis_password
    volumes:
      - redis_data:/data
    networks:
      - clarity_network

  nginx:
    image: nginx:1.19
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ../ssl:/etc/ssl:ro
    depends_on:
      - web
    networks:
      - clarity_network

volumes:
  postgres_data:
  redis_data:

networks:
  clarity_network:
    driver: bridge

# File: docker/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    
    # Gzip configuration
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    server {
        listen 80;
        server_name clarity.ai www.clarity.ai;
        
        # Redirect all HTTP requests to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name clarity.ai www.clarity.ai;
        
        ssl_certificate /etc/ssl/certs/clarity.crt;
        ssl_certificate_key /etc/ssl/private/clarity.key;
        
        location / {
            proxy_pass http://web:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Static files
        location /static/ {
            alias /app/static/;
            expires 1d;
            add_header Cache-Control "public, no-transform";
        }
        
        # Media files
        location /media/ {
            alias /app/media/;
            expires 1d;
            add_header Cache-Control "public, no-transform";zzzzzzzs
        }
        
        # Health check
        location /health {
            access_log off;
            return 200 'OK';
            add_header Content-Type text/plain;
        }
    }
}
