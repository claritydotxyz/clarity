from typing import Any, Dict, List, Optional
import re
from datetime import datetime
import structlog

logger = structlog.get_logger()

class DataValidator:
    """Validate data formats and content."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_password(password: str) -> tuple[bool, Optional[str]]:
        """Validate password strength."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain lowercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain digit"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain special character"
        return True, None

    @staticmethod
    def validate_date_format(date_str: str) -> bool:
        """Validate date string format."""
        try:
            datetime.fromisoformat(date_str)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any],
        required: List[str]
    ) -> tuple[bool, List[str]]:
        """Validate required fields presence."""
        missing = [field for field in required if not data.get(field)]
        return len(missing) == 0, missing

    @staticmethod
    def validate_numeric_range(
        value: Union[int, float],
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None
    ) -> bool:
        """Validate numeric value within range."""
        if min_value is not None and value < min_value:
            return False
        if max_value is not None and value > max_value:
            return False
        return True

    @staticmethod
    def validate_string_length(
        text: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> bool:
        """Validate string length within range."""
        if min_length is not None and len(text) < min_length:
            return False
        if max_length is not None and len(text) > max_length:
            return False
        return True

    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize input string."""
        # Remove potentially dangerous characters
        text = re.sub(r'[<>\'"]', '', text)
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
