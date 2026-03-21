import json
import math
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.chat_log import ChatLog
from ..models.user import User
from ..schemas.chat_log import ChatLogResponse, ChatSessionGroup
from ..schemas.agriculture import PaginatedResponse


def safe_json(value):
    """安全解析 JSON 字串"""
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


class ChatLogService:
    @staticmethod
    def list_sessions(
        db: Session, page: int, page_size: int, user_id: int = None
    ) -> PaginatedResponse:
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
            first_user_msg = (
                db.query(ChatLog.content)
                .filter(ChatLog.session_id == r.session_id, ChatLog.role == "user")
                .order_by(ChatLog.created_at.asc())
                .first()
            )
            first_query = first_user_msg.content[:50] if first_user_msg else ""

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

    @staticmethod
    def get_session_messages(db: Session, session_id: str) -> list[ChatLogResponse]:
        """取得某 session 所有訊息"""
        logs = (
            db.query(ChatLog, User.username)
            .join(User, ChatLog.user_id == User.id)
            .filter(ChatLog.session_id == session_id)
            .order_by(ChatLog.created_at.asc())
            .all()
        )

        if not logs:
            raise ValueError("找不到該對話紀錄")

        return [
            ChatLogResponse(
                id=log.id,
                user_id=log.user_id,
                username=username,
                session_id=log.session_id,
                role=log.role,
                content=log.content,
                tool_calls=safe_json(log.tool_calls),
                images=safe_json(log.images),
                created_at=log.created_at,
            )
            for log, username in logs
        ]

    @staticmethod
    def delete_session(db: Session, session_id: str) -> None:
        """刪除整個 session 的對話紀錄"""
        count = db.query(ChatLog).filter(ChatLog.session_id == session_id).delete()
        db.commit()
        if count == 0:
            raise ValueError("找不到該對話紀錄")
