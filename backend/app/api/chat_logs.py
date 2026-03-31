from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..schemas.chat_log import ChatLogResponse, ChatSessionGroup
from ..schemas.agriculture import PaginatedResponse
from ..services.chat_log import ChatLogService
from .auth import get_current_admin_user


class BatchDeleteRequest(BaseModel):
    session_ids: List[str]

router = APIRouter(prefix="/api/admin/chat-logs", tags=["chat-logs"])


@router.get("/", response_model=PaginatedResponse[ChatSessionGroup])
def list_chat_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user_id: int = Query(None),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin_user),
):
    """分頁列出對話 sessions（按 session_id 分組）"""
    return ChatLogService.list_sessions(db, page, page_size, user_id)


@router.get("/{session_id}", response_model=list[ChatLogResponse])
def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin_user),
):
    """取得某 session 所有訊息"""
    try:
        return ChatLogService.get_session_messages(db, session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/batch-delete", status_code=status.HTTP_204_NO_CONTENT)
def batch_delete_sessions(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin_user),
):
    """批次刪除多個 session 的對話紀錄"""
    if not request.session_ids:
        raise HTTPException(status_code=400, detail="請選擇要刪除的對話")
    ChatLogService.delete_sessions_batch(db, request.session_ids)
    return None


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin_user),
):
    """刪除整個 session 的對話紀錄"""
    try:
        ChatLogService.delete_session(db, session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None
