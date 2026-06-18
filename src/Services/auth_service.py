from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.user import User
from src.security.jwt_handler import create_access_token
from src.security.password import hash_password, verify_password
from src.Services.user_service import get_user_by_email


def register_user(db: Session, name: str, email: str, password: str) -> User:
    if get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role="USER",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str) -> dict:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user_id=user.id, role=user.role)
    return {"access_token": token, "token_type": "bearer"}
