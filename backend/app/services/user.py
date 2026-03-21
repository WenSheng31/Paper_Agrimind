from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.user import UserCreate, AdminCreateUser
from ..core.security import get_password_hash, verify_password
from typing import Optional, List


class UserService:
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def _get_user_or_raise(db: Session, user_id: int) -> User:
        """取得用戶，找不到則拋出 ValueError"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError("找不到該用戶")
        return user

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        # 檢查 email 是否已存在
        if UserService.get_user_by_email(db, user_data.email):
            raise ValueError("該 Email 已被註冊")

        # 檢查 username 是否已存在
        if UserService.get_user_by_username(db, user_data.username):
            raise ValueError("用戶名已被使用")

        # 建立新用戶
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        user = UserService.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    # === 管理員操作 ===

    @staticmethod
    def get_all_users(db: Session) -> List[User]:
        """取得所有用戶列表"""
        return db.query(User).all()

    @staticmethod
    def admin_create_user(db: Session, user_data: AdminCreateUser) -> User:
        """管理員新增帳號，支援設定 is_admin"""
        user = UserService.create_user(db, user_data)
        if user_data.is_admin:
            user.is_admin = True
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int, current_admin_id: int) -> None:
        """刪除用戶"""
        if user_id == current_admin_id:
            raise ValueError("不能刪除自己的帳號")
        user = UserService._get_user_or_raise(db, user_id)
        if user.is_admin:
            admin_count = db.query(User).filter(User.is_admin == True).count()
            if admin_count <= 1:
                raise ValueError("無法刪除最後一位管理員")
        db.delete(user)
        db.commit()

    @staticmethod
    def toggle_active(db: Session, user_id: int, current_admin_id: int) -> User:
        """停用/啟用用戶"""
        if user_id == current_admin_id:
            raise ValueError("不能停用自己的帳號")
        user = UserService._get_user_or_raise(db, user_id)
        user.is_active = not user.is_active
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def toggle_admin(db: Session, user_id: int, current_admin_id: int) -> User:
        """切換用戶管理員權限"""
        if user_id == current_admin_id:
            raise ValueError("不能變更自己的管理員權限")
        user = UserService._get_user_or_raise(db, user_id)
        if user.is_admin:
            admin_count = db.query(User).filter(User.is_admin == True).count()
            if admin_count <= 1:
                raise ValueError("無法降級最後一位管理員")
        user.is_admin = not user.is_admin
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def reset_password(db: Session, user_id: int, password: str, current_admin_id: int) -> User:
        """重設用戶密碼"""
        if user_id == current_admin_id:
            raise ValueError("不能透過此功能重設自己的密碼")
        user = UserService._get_user_or_raise(db, user_id)
        user.hashed_password = get_password_hash(password)
        db.commit()
        db.refresh(user)
        return user


user_service = UserService()
