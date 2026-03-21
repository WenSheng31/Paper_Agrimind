from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..schemas.user import UserResponse, ResetPasswordRequest, AdminCreateUser
from ..services.user import user_service
from .auth import get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    body: AdminCreateUser,
    db: Session = Depends(get_db),
    _current_admin=Depends(get_current_admin_user)
):
    """管理員新增帳號"""
    try:
        return user_service.admin_create_user(db, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    _current_admin=Depends(get_current_admin_user)
):
    """獲取所有用戶列表 (僅管理員)"""
    return user_service.get_all_users(db)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_user)
):
    """刪除用戶 (僅管理員)"""
    try:
        user_service.delete_user(db, user_id, current_admin.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return None


@router.put("/users/{user_id}/toggle-active", response_model=UserResponse)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_user)
):
    """停用/啟用用戶 (僅管理員)"""
    try:
        return user_service.toggle_active(db, user_id, current_admin.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/users/{user_id}/toggle-admin", response_model=UserResponse)
def toggle_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_user)
):
    """切換用戶管理員權限 (僅管理員)"""
    try:
        return user_service.toggle_admin(db, user_id, current_admin.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/users/{user_id}/reset-password", response_model=UserResponse)
def reset_user_password(
    user_id: int,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_user)
):
    """重設用戶密碼 (僅管理員)"""
    try:
        return user_service.reset_password(db, user_id, body.password, current_admin.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
