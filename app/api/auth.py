from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserMeResponse

router = APIRouter(prefix='/auth', tags=['auth'])


def _normalize_display_name(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _auth_response(user: User) -> AuthResponse:
    token = create_access_token(user.id, user.email)
    return AuthResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        access_token=token,
    )


@router.post('/register', response_model=AuthResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400,
            detail={'code': 'email_taken', 'message': 'Пользователь с таким email уже зарегистрирован.'},
        )

    user = User(
        email=email,
        password_hash=hash_password(body.password),
        display_name=_normalize_display_name(body.display_name),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return _auth_response(user)


@router.post('/login', response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail={'code': 'invalid_credentials', 'message': 'Неверный email или пароль.'},
        )

    return _auth_response(user)


@router.get('/me', response_model=UserMeResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserMeResponse(
        user_id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
    )
