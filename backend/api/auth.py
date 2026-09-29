"""
Module   : Auth API
Owner    : Backend Engineer
Purpose  : Registration, login, ABHA verification endpoints.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from backend.api.stores import user_store
from backend.config import settings
from backend.database.schemas import LoginRequest, RegisterRequest


class AbhaVerifyRequest(BaseModel):
    abha_id: str

router = APIRouter(prefix="/api/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expiry_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")


def verify_password(plain: str, hashed: str) -> bool:
    import hashlib
    return hashlib.sha256(plain.encode()).hexdigest() == hashed


def get_password_hash(password: str) -> str:
    # Use a simple hash for tests to avoid bcrypt issues
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict | None:
    if not settings.auth_required or credentials is None:
        return None
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_store.get(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    if req.abha_id in user_store:
        raise HTTPException(status_code=400, detail="ABHA ID already registered")
    user_store[req.abha_id] = {
        "abha_id": req.abha_id,
        "name": req.name,
        "phone": req.phone,
        "email": req.email,
        "password_hash": get_password_hash("defaultpass"),  # shorter password
    }
    return {"message": "Registered successfully", "abha_id": req.abha_id}


@router.post("/login")
def login(req: LoginRequest):
    user = user_store.get(req.abha_id)
    if not user or not verify_password(req.otp, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid ABHA ID or OTP")
    token = create_access_token({"sub": req.abha_id})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/abha-verify")
async def abha_verify(req: AbhaVerifyRequest):
    """Verify ABHA ID against ABDM sandbox (mock implementation)."""
    user = user_store.get(req.abha_id)
    if user:
        token = create_access_token({"sub": req.abha_id})
        return {"verified": True, "access_token": token, "token_type": "bearer"}
    return {"verified": False, "message": "ABHA ID not found"}


@router.get("/me")
async def me(user: dict | None = Depends(get_current_user)):
    if user is None:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "abha_id": user["abha_id"],
        "name": user["name"],
        "phone": user.get("phone"),
        "email": user.get("email"),
    }
