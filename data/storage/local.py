from typing import Any, Dict, List, Optional
import os
import json
from datetime import datetime
import structlog

logger = structlog.get_logger()

class LocalStorage:
    """Local file-based data storage."""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    async def save(self, data: Dict, filename: str):
        """Save data to local file."""
        try:
            path = os.path.join(self.base_path, filename)
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info("local_storage.save_success", path=path)
            
        except Exception as e:
            logger.error("local_storage.save_failed", path=path, error=str(e))
            raise

    async def load(self, filename: str) -> Dict:
        """Load data from local file."""
        try:
            path = os.path.join(self.base_path, filename)
            
            with open(path, 'r') as f:
                data = json.load(f)
                
            logger.info("local_storage.load_success", path=path)
            return data
            
        except Exception as e:
            logger.error("local_storage.load_failed", path=path, error=str(e))
