from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatLogResponse(BaseModel):
    id: int
    user_id: int
    username: str
    session_id: str
    role: str
    content: str
    tool_calls: Optional[list[dict]] = None
    images: Optional[list[dict]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionGroup(BaseModel):
    session_id: str
    user_id: int
    username: str
    message_count: int
    last_active: datetime
    first_query: str
