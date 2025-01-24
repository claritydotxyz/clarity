from typing import Any, Dict, Optional
from datetime import datetime
import json
from cryptography.fernet import Fernet
from clarity.utils.crypto.encryption import get_encryption_key
import structlog

logger = structlog.get_logger()

class EncryptedStorage:
    """Encrypted data storage."""
    
    def __init__(self, key: Optional[str] = None):
        self.key = key or get_encryption_key()
        self.cipher = Fernet(self.key)

    async def save(self, data: Dict, path: str):
        """Save encrypted data to file."""
        try:
            # Serialize data
            json_data = json.dumps(data)
            
            # Encrypt
            encrypted_data = self.cipher.encrypt(json_data.encode())
            
            # Save to file
            with open(path, 'wb') as f:
                f.write(encrypted_data)
                
            logger.info("encrypted_storage.save_success", path=path)
            
        except Exception as e:
            logger.error("encrypted_storage.save_failed", path=path, error=str(e))
            raise

    async def load(self, path: str) -> Dict:
        """Load and decrypt data from file."""
        try:
            # Read encrypted data
            with open(path, 'rb') as f:
                encrypted_data = f.read()
                
            # Decrypt
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            # Parse JSON
            data = json.loads(decrypted_data)
            
            logger.info("encrypted_storage.load_success", path=path)
            return data
            
        except Exception as e:
            logger.error("encrypted_storage.load_failed", path=path, error=str(e))
            raise

    def rotate_key(self, new_key: str):
        """Rotate encryption key."""
        self.key = new_key
        self.cipher = Fernet(new_key)
        logger.info("encrypted_storage.key_rotated")
