from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from typing import Dict
from app.services.auth_service import auth_service
from app.schemas.auth import (
    GoogleOAuthRequest,
    GoogleOAuthResponse,
    AuthURLResponse,
    UserResponse,
    GoogleUserInfo,
)
from app.utils.user_storage import user_storage
from app.dependencies import get_current_user

router = APIRouter()


@router.get("/google/url", response_model=AuthURLResponse)
async def get_google_auth_url():
    """Get Google OAuth authorization URL"""
    auth_url = auth_service.get_google_oauth_url()
    return AuthURLResponse(auth_url=auth_url)


@router.post("/google", response_model=GoogleOAuthResponse)
async def google_oauth(request: GoogleOAuthRequest):
    """Exchange Google OAuth code for access token"""
    try:
        # Exchange code for tokens
        tokens = await auth_service.exchange_code_for_tokens(request.code)

        # Get user info from Google
        user_info = await auth_service.get_user_info(tokens["access_token"])

        # Create GoogleUserInfo object
        google_user = GoogleUserInfo(
            id=user_info["id"],
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info.get("picture"),
            given_name=user_info.get("given_name"),
            family_name=user_info.get("family_name"),
        )

        # Create or update user in storage
        user_data = user_storage.create_or_update_user(google_user, tokens)

        # Create our internal JWT token
        jwt_token = auth_service.create_access_token(
            data={"sub": user_data["id"], "email": user_data["email"]}
        )

        # Return response
        return GoogleOAuthResponse(
            access_token=jwt_token,
            token_type="bearer",
            expires_in=1800,  # 30 minutes
            user=UserResponse(**user_data),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current authenticated user"""
    return UserResponse(**current_user)


@router.post("/refresh")
async def refresh_token(current_user: Dict = Depends(get_current_user)):
    """Refresh Google access token"""
    try:
        # Get user's refresh token
        user_tokens = user_storage.get_user_tokens(current_user["id"])

        if not user_tokens or not user_tokens.get("refresh_token"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No refresh token available. Please re-authenticate.",
            )

        # Refresh the token
        new_tokens = await auth_service.refresh_access_token(
            user_tokens["refresh_token"]
        )

        # Update stored tokens
        user_storage.update_user_tokens(current_user["id"], new_tokens)

        return {"message": "Token refreshed successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token refresh failed: {str(e)}",
        )


@router.post("/logout")
async def logout(current_user: Dict = Depends(get_current_user)):
    """Logout current user"""
    # In a real app, you might want to revoke the Google tokens
    # For now, we'll just return a success message
    # The frontend should remove the JWT token from storage
    return {"message": "Logged out successfully"}
