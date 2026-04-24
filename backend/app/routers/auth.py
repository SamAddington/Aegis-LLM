"""Authentication router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from app.config import settings
from app.services import auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: dict


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=3, max_length=256)
    email: str | None = Field(default=None, max_length=256)


def _client_ip(request: Request) -> str:
    # Trust the nearest proxy's X-Forwarded-For (nginx/docker) and fall back
    # to the raw peer. Not a security boundary - just used for rate limiting.
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    auth.note_login_attempt(_client_ip(request), form.username)
    user = auth.authenticate(form.username, form.password)
    token = auth.create_access_token(sub=user.username, role=user.role)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.jwt_expires_minutes,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    )


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest) -> TokenResponse:
    if not settings.allow_registration:
        raise HTTPException(403, "Self-registration is disabled. Ask an admin to create your account.")
    user = auth.create_user(req.username, req.password, role="student", email=req.email)
    token = auth.create_access_token(sub=user.username, role=user.role)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.jwt_expires_minutes,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    )


@router.get("/me")
async def me(user: auth.User = Depends(auth.current_user)) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at,
        "last_login": user.last_login,
    }


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=3, max_length=256)


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    user: auth.User = Depends(auth.current_user),
) -> dict:
    # Re-authenticate with the current password to prove the session isn't
    # just a stolen token (mild token-replay hardening).
    auth.authenticate(user.username, req.current_password)
    auth.change_password(user.id, req.new_password)
    return {"status": "ok"}


@router.get("/config")
async def config() -> dict:
    """Public-ish bootstrap info the login page needs before authenticating."""
    return {
        "allow_registration": settings.allow_registration,
        "jwt_expires_minutes": settings.jwt_expires_minutes,
    }
