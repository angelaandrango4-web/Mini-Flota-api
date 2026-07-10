from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt

from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        email = payload.get("sub")

        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        return email

    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")