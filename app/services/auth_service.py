from datetime import datetime, timedelta, UTC

import bcrypt
import jwt
from passlib.context import CryptContext

from app.config import settings

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )

def create_access_token(email: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=30)
    payload = {"sub": email, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")