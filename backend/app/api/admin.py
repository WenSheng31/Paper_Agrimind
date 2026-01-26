from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..schemas.user import UserResponse
from ..services.user import user_service
from ..models.user import User
from .auth import get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    _current_admin=Depends(get_current_admin_user)
):
    """獲取所有用戶列表 (僅管理員)"""
    users = db.query(User).all()
    return users


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_user)
):
    """刪除用戶 (僅管理員)"""
    # 不能刪除自己
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能刪除自己的帳號"
        )

    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到該用戶"
        )

    db.delete(user)
    db.commit()
    return None


@router.put("/users/{user_id}/toggle-active", response_model=UserResponse)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin_user)
):
    """停用/啟用用戶 (僅管理員)"""
    # 不能停用自己
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能停用自己的帳號"
        )

    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到該用戶"
        )

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user
