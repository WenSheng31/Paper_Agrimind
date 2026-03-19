from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    tool_calls = Column(Text, nullable=True)  # JSON
    images = Column(Text, nullable=True)  # JSON: [{"data": "base64...", "media_type": "image/jpeg"}]
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
