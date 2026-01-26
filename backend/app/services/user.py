from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.user import UserCreate
from ..core.security import get_password_hash, verify_password
from typing import Optional


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


user_service = UserService()
