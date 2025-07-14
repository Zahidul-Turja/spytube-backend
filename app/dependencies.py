from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
from app.services.auth_service import auth_service
from app.utils.user_storage import user_storage

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    """Get current authenticated user from JWT token"""
    try:
        # Verify the JWT token
        payload = auth_service.verify_token(credentials.credentials)
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )

        # Get user from storage
        user = user_storage.get_user(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Dict]:
    """Get current user if authenticated, None otherwise"""
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def get_user_google_tokens(
    current_user: Dict = Depends(get_current_user),
) -> Dict:
    """Get current user's Google tokens"""
    tokens = user_storage.get_user_tokens(current_user["id"])

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google tokens not found. Please re-authenticate.",
        )

    return tokens
