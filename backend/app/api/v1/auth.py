from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginIn(BaseModel):
    username: str

@router.post("/login", response_model=Token)
async def login(payload: LoginIn):
    # demo: accept any username, issue token (for real app implement password check)
    to_encode = {"sub": payload.username}
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire.isoformat()})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}
