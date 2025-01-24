import hashlib
import bcrypt
from typing import Optional
from clarity.config.settings import settings
import structlog

logger = structlog.get_logger()

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    try:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()
    except Exception as e:
        logger.error("password_hashing.failed", error=str(e))
        raise

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode(),
            hashed_password.encode()
        )
    except Exception as e:
        logger.error("password_verification.failed", error=str(e))
        return False

def get_content_hash(content: bytes) -> str:
    """Get SHA-256 hash of content."""
    return hashlib.sha256(content).hexdigest()
