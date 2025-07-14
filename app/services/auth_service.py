import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import HTTPException, status
from typing import Dict, Optional
import jwt
from datetime import datetime, timedelta
from app.core.config import settings


class AuthService:
    def __init__(self):
        self.google_client_id = settings.GOOGLE_CLIENT_ID
        self.google_client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.google_token_url = "https://oauth2.googleapis.com/token"
        self.google_userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_google_oauth_url(self) -> str:
        """Generate Google OAuth authorization URL"""
        scopes = [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/yt-analytics.readonly",
        ]

        params = {
            "client_id": self.google_client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
        }

        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])

        return f"{base_url}?{query_string}"

    async def exchange_code_for_tokens(self, code: str) -> Dict:
        """Exchange authorization code for access and refresh tokens"""
        async with httpx.AsyncClient() as client:
            data = {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
            }

            response = await client.post(self.google_token_url, data=data)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for tokens",
                )

            return response.json()

    async def get_user_info(self, access_token: str) -> Dict:
        """Get user information from Google"""
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(self.google_userinfo_url, headers=headers)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to get user information",
                )

            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh access token using refresh token"""
        async with httpx.AsyncClient() as client:
            data = {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }

            response = await client.post(self.google_token_url, data=data)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh access token",
                )

            return response.json()

    def create_access_token(
        self, data: Dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    def verify_token(self, token: str) -> Dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )


# Create singleton instance
auth_service = AuthService()
