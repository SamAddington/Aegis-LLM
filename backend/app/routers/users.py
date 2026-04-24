"""Admin users router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services import auth

router = APIRouter(prefix="/api/users", tags=["users"])


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=3, max_length=256)
    role: str = Field(default="student", pattern="^(admin|student)$")
    email: str | None = None


class UpdateRoleRequest(BaseModel):
    role: str = Field(..., pattern="^(admin|student)$")


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=3, max_length=256)


def _serialize(u: auth.User) -> dict:
    return {
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "created_at": u.created_at,
        "last_login": u.last_login,
    }


@router.get("/")
async def list_users(_: auth.User = Depends(auth.admin_user)) -> list[dict]:
    return [_serialize(u) for u in auth.list_users()]


@router.post("/", status_code=201)
async def create_user(
    req: CreateUserRequest, _: auth.User = Depends(auth.admin_user)
) -> dict:
    user = auth.create_user(req.username, req.password, role=req.role, email=req.email)
    return _serialize(user)


@router.patch("/{user_id}/role")
async def update_role(
    user_id: int,
    req: UpdateRoleRequest,
    _: auth.User = Depends(auth.admin_user),
) -> dict:
    return _serialize(auth.update_user_role(user_id, req.role))


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    req: ResetPasswordRequest,
    _: auth.User = Depends(auth.admin_user),
) -> dict:
    auth.change_password(user_id, req.new_password)
    return {"status": "ok"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int, current: auth.User = Depends(auth.admin_user)
) -> dict:
    if current.id == user_id:
        raise HTTPException(409, "Admins cannot delete their own account.")
    auth.delete_user(user_id)
    return {"status": "deleted", "id": user_id}
