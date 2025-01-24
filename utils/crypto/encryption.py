import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog

logger = structlog.get_logger()

def generate_key() -> bytes:
    """Generate a new encryption key."""
    return Fernet.generate_key()

def derive_key(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """Derive encryption key from password."""
    salt = salt or os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def encrypt_data(data: bytes, key: bytes) -> bytes:
    """Encrypt data using Fernet encryption."""
    try:
        f = Fernet(key)
        return f.encrypt(data)
    except Exception as e:
        logger.error("encryption.failed", error=str(e))
        raise

def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    """Decrypt Fernet-encrypted data."""
    try:
        f = Fernet(key)
        return f.decrypt(encrypted_data)
    except Exception as e:
        logger.error("decryption.failed", error=str(e))
        raise
