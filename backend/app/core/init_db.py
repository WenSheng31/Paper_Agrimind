from sqlalchemy import text
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from ..models.user import User
from ..models.agriculture import Farm, SensorData, Operation, ImageRecord, ImageRecordFile
from ..models.knowledge import KnowledgeDocument
from ..models.chat_log import ChatLog


def init_db():
    """初始化資料庫：建立資料表"""
    # 0. 啟用 pgvector 擴充
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # 1. 建立所有資料表
    Base.metadata.create_all(bind=engine)

    print("Database initialized. Admin will be assigned via ADMIN_EMAILS env var on first Google login.")


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization completed!")
