from fastapi import APIRouter, Depends, HTTPException
from app.services.auth_service import auth_service
from app.utils.user_storage import user_storage


async def get_valid_access_token(user_id: str) -> str:
    tokens = user_storage.get_user_tokens(user_id)
    if not tokens:
        raise HTTPException(status_code=401, detail="No token found")

    access_token = tokens["access_token"]
    expires_in = tokens.get("expires_in")

    # Optional: Track expiration timestamp
    # if token is expired → refresh
    refreshed = await auth_service.refresh_access_token(tokens["refresh_token"])

    # Save new token
    user_storage.update_user_tokens(user_id, refreshed)
    return refreshed["access_token"]
