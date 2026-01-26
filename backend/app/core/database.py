from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# 建立同步引擎 (PostgreSQL 使用 psycopg2)
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=5,              # 連接池大小
    max_overflow=10,          # 最大溢出連接數
    pool_pre_ping=True,       # 每次連接前檢查連接是否有效
    pool_recycle=3600,        # 連接回收時間（秒），防止連接過期
    echo=False                # 設為 True 可以看到 SQL 語句（開發時有用）
)

# 建立 Session 工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 類別供所有模型繼承
Base = declarative_base()


# 依賴注入函數
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
