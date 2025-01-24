from typing import Optional
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from clarity.config.settings import settings
import structlog

logger = structlog.get_logger()

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")
        
        if not credentials.scheme == "Bearer":
            raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
        
        try:
            payload = jwt.decode(
                credentials.credentials, 
                settings.SECRET_KEY.get_secret_value(),
                algorithms=[settings.ALGORITHM]
            )
            
            # Add user info to request state
            request.state.user_id = payload.get("sub")
            request.state.user_role = payload.get("role", "user")
            
            return credentials.credentials
            
        except JWTError as e:
            logger.error("auth.token.invalid", error=str(e))
            raise HTTPException(
                status_code=403,
                detail="Could not validate credentials"
            )
