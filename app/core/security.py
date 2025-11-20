from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from app.core.config import settings
import jwt
from jwt.exceptions import InvalidTokenError

password_hash = PasswordHash.recommended()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def create_access_token(data: dict, expires: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        return None