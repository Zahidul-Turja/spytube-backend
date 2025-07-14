from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class GoogleOAuthRequest(BaseModel):
    code: str


class GoogleOAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    picture: Optional[str] = None
    google_id: str
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthURLResponse(BaseModel):
    auth_url: str
    state: Optional[str] = None


# For internal use (not exposed in API)
class GoogleTokens(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int
    token_type: str = "Bearer"


class GoogleUserInfo(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None


# Update forward references
GoogleOAuthResponse.model_rebuild()
