import math
import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..core.database import get_db
from ..models.chat_log import ChatLog
from ..models.user import User
from ..schemas.chat_log import ChatLogResponse, ChatSessionGroup
from ..schemas.agriculture import PaginatedResponse
from .auth import get_current_admin_user

router = APIRouter(prefix="/api/admin/chat-logs", tags=["chat-logs"])


def _safe_json(value):
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


@router.get("/", response_model=PaginatedResponse[ChatSessionGroup])
def list_chat_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user_id: int = Query(None),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin_user),
):
    """分頁列出對話 sessions（按 session_id 分組）"""
    base = db.query(ChatLog)
    if user_id:
        base = base.filter(ChatLog.user_id == user_id)

    query = (
        base.with_entities(
            ChatLog.session_id,
            ChatLog.user_id,
            User.username,
            func.count(ChatLog.id).label("message_count"),
            func.max(ChatLog.created_at).label("last_active"),
            func.min(ChatLog.id).label("first_id"),
        )
        .join(User, ChatLog.user_id == User.id)
        .group_by(ChatLog.session_id, ChatLog.user_id, User.username)
        .order_by(func.max(ChatLog.created_at).desc())
    )

    total = query.count()
    results = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for r in results:
        # 取得該 session 第一筆 user 訊息作為 title
        first_user_msg = (
            db.query(ChatLog.content)
            .filter(ChatLog.session_id == r.session_id, ChatLog.role == "user")
            .order_by(ChatLog.created_at.asc())
            .first()
        )
        first_query = (first_user_msg.content[:50] if first_user_msg else "")

        items.append(
            ChatSessionGroup(
                session_id=r.session_id,
                user_id=r.user_id,
                username=r.username,
                message_count=r.message_count,
                last_active=r.last_active,
                first_query=first_query,
            )
        )

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{session_id}", response_model=list[ChatLogResponse])
def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin_user),
):
    """取得某 session 所有訊息"""
    logs = (
        db.query(ChatLog, User.username)
        .join(User, ChatLog.user_id == User.id)
        .filter(ChatLog.session_id == session_id)
        .order_by(ChatLog.created_at.asc())
        .all()
    )

    if not logs:
        raise HTTPException(status_code=404, detail="找不到該對話紀錄")

    return [
        ChatLogResponse(
            id=log.id,
            user_id=log.user_id,
            username=username,
            session_id=log.session_id,
            role=log.role,
            content=log.content,
            tool_calls=_safe_json(log.tool_calls),
            images=_safe_json(log.images),
            created_at=log.created_at,
        )
        for log, username in logs
    ]


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin_user),
):
    """刪除整個 session 的對話紀錄"""
    count = db.query(ChatLog).filter(ChatLog.session_id == session_id).delete()
    db.commit()
    if count == 0:
        raise HTTPException(status_code=404, detail="找不到該對話紀錄")
    return None
