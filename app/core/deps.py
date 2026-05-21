from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != 'bearer':
        raise HTTPException(
            status_code=401,
            detail={'code': 'unauthorized', 'message': 'Требуется авторизация. Передайте Bearer token.'},
        )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = str(payload.get('sub', ''))
    except Exception:
        raise HTTPException(
            status_code=401,
            detail={'code': 'invalid_token', 'message': 'Недействительный или просроченный токен.'},
        )

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=401,
            detail={'code': 'user_not_found', 'message': 'Пользователь не найден.'},
        )
    return user
