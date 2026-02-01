from sqlalchemy import text
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from ..models.user import User
from ..models.knowledge import KnowledgeDocument
from .security import get_password_hash


def init_db():
    """初始化資料庫：建立資料表並預設管理員"""
    # 0. 啟用 pgvector 擴充
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # 1. 建立所有資料表
    Base.metadata.create_all(bind=engine)
    
    # 2. 建立預設資料 (種子資料)
    db = SessionLocal()
    try:
        # 檢查是否已有管理員
        admin_user = db.query(User).filter(User.email == "admin@admin.com").first()
        if not admin_user:
            print("Creating default admin user...")
            admin_user = User(
                username="admin",
                email="admin@admin.com",
                hashed_password=get_password_hash("admin123"),
                is_admin=True,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("Default admin created: admin@admin.com / admin123")
        else:
            print("Admin user already exists.")
            
    except Exception as e:
        print(f"Error initializing data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization completed!")
