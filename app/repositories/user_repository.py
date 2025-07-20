# app/repositories/user_repository.py
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import GoogleUserInfo
from typing import Dict


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def create_or_update_user(
    db: Session, google_user: GoogleUserInfo, tokens: Dict
) -> User:
    user = get_user_by_email(db, google_user.email)

    if user:
        user.name = google_user.name
        user.picture = google_user.picture
        user.google_id = google_user.id
        user.tokens = tokens
    else:
        user = User(
            email=google_user.email,
            name=google_user.name,
            picture=google_user.picture,
            google_id=google_user.id,
            tokens=tokens,
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    return user


def update_tokens(db: Session, user_id: int, tokens: Dict):
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    user.tokens = tokens
    db.commit()
    return user.tokens
