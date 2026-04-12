from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from ..core.database import get_db
from ..core.security import create_access_token, verify_token
from ..core.config import settings
from ..schemas.user import GoogleLoginRequest, UserResponse, Token
from ..services.user import user_service
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/api/auth", tags=["auth"])

security = HTTPBearer()


# 依賴注入: 獲取當前用戶
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="憑證無效或已過期"
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="憑證內容錯誤"
        )
    user = user_service.get_user_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶不存在"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="該帳號已被停用"
        )
    return user


# 依賴注入: 獲取當前管理員用戶
def get_current_admin_user(
    current_user=Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足，需要管理員權限"
        )
    return current_user


@router.post("/login/google", response_model=Token)
def google_login(body: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Google 登入"""
    # 1. 驗證 Google ID Token
    try:
        idinfo = id_token.verify_oauth2_token(
            body.credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google 憑證無效"
        )

    # 2. 取得用戶資訊
    google_sub = idinfo["sub"]
    email = idinfo["email"]
    name = idinfo.get("name", email.split("@")[0])

    # 3. 查找或建立用戶
    user = user_service.find_or_create_google_user(db, google_sub, email, name)

    # 4. 檢查是否被停用
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="該帳號已被停用"
        )

    # 5. 自動升級管理員
    if email in settings.admin_emails_list and not user.is_admin:
        user_service.set_admin(db, user)

    # 6. 建立 JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return current_user
