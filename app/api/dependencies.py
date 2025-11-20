from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.user_services import get_user_by_username
from ..core.security import decode_token
from ..schemas.user import TokenData, UserOut

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_token_from_request(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> str:
    """
    Lấy token từ:
    1. Authorization header (Bearer token)
    2. access_token cookie
    3. access_token query parameter
    """
    # Ưu tiên header bearer token
    if token:
        return token
    
    # Thử lấy từ cookie
    token = request.cookies.get("access_token")
    if token:
        return token
    
    # Thử lấy từ query parameter
    token = request.query_params.get("token")
    if token:
        return token
    
    return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> UserOut:
    token = get_token_from_request(request)
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_active_user(current_user = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
