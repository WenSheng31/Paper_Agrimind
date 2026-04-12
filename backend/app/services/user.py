from sqlalchemy.orm import Session
from ..models.user import User
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
    def find_or_create_google_user(db: Session, google_id: str, email: str, name: str) -> User:
        """透過 Google 資訊查找或建立用戶"""
        # 1. 以 google_id 查找
        user = db.query(User).filter(User.google_id == google_id).first()
        if user:
            return user

        # 2. 以 email 查找（銜接舊帳號）
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
            db.commit()
            db.refresh(user)
            return user

        # 3. 建立新帳號
        base_username = name.replace(" ", "").lower()[:20]
        username = base_username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}{counter}"
            counter += 1

        new_user = User(
            username=username,
            email=email,
            google_id=google_id,
            hashed_password=None,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def set_admin(db: Session, user: User) -> None:
        """設定用戶為管理員"""
        user.is_admin = True
        db.commit()

    # === 管理員操作 ===

    @staticmethod
    def get_all_users(db: Session) -> List[User]:
        """取得所有用戶列表"""
        return db.query(User).all()

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


user_service = UserService()
