from typing import Dict, Optional
from datetime import datetime
from app.schemas.auth import GoogleUserInfo


class InMemoryUserStorage:
    """Temporary in-memory storage for users (replace with database later)"""

    def __init__(self):
        self.users: Dict[str, Dict] = {}
        self.user_tokens: Dict[str, Dict] = {}

    def create_or_update_user(self, google_user: GoogleUserInfo, tokens: Dict) -> Dict:
        """Create or update user with Google info and tokens"""
        user_data = {
            "id": google_user.id,
            "email": google_user.email,
            "name": google_user.name,
            "picture": google_user.picture,
            "google_id": google_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Update existing user or create new one
        if google_user.id in self.users:
            user_data["created_at"] = self.users[google_user.id]["created_at"]
            user_data["updated_at"] = datetime.utcnow()

        self.users[google_user.id] = user_data
        self.user_tokens[google_user.id] = {
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens.get("expires_in"),
            "token_type": tokens.get("token_type", "Bearer"),
        }

        return user_data

    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        return self.users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        for user in self.users.values():
            if user["email"] == email:
                return user
        return None

    def get_user_tokens(self, user_id: str) -> Optional[Dict]:
        """Get user's Google tokens"""
        return self.user_tokens.get(user_id)

    def update_user_tokens(self, user_id: str, tokens: Dict):
        """Update user's tokens"""
        if user_id in self.user_tokens:
            self.user_tokens[user_id].update(tokens)
        else:
            self.user_tokens[user_id] = tokens


# Create singleton instance
user_storage = InMemoryUserStorage()
