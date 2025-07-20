from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
from app.services.auth_service import auth_service
from app.utils.user_storage import user_storage
from app.database import SessionLocal
from app.repositories import user_repository
from sqlalchemy.orm import session
from sqlalchemy.orm import Session

security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Dict:
    try:
        payload = auth_service.verify_token(credentials.credentials)
        user_id = payload.get("sub")

        print("payload", payload)

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )

        user = user_repository.get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        user_dict = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "google_id": user.google_id,
            "tokens": user.tokens,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

        tokens = user_storage.get_user_tokens(user_id) or {}
        user_with_tokens = {**user_dict, **tokens}

        return user_with_tokens

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
