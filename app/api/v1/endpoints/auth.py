from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.database import database
from app.schemas.user import TokenResponse
from app.services.auth_service import verify_password, create_access_token

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await database["users"].find_one({"email": form_data.username})
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = create_access_token(form_data.username)
    return TokenResponse(access_token=token)