import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .core.config import settings
from .core.init_db import init_db
from .api import auth, admin, agriculture, ai, knowledge, image_records, chat_logs

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # 啟動時連接 MCP 服務器
    await ai.mcp_client.connect()
    yield
    # 關閉時清理 MCP 資源
    await ai.mcp_client.cleanup()

app = FastAPI(title="Argi API", version="1.0.0", lifespan=lifespan)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 上傳目錄
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# 註冊路由
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(agriculture.router)
app.include_router(ai.router)
app.include_router(knowledge.router)
app.include_router(image_records.router)
app.include_router(chat_logs.router)

@app.get("/uploads/{file_path:path}")
def serve_upload(file_path: str):
    full_path = os.path.join(settings.UPLOAD_DIR, file_path)
    if not os.path.isfile(full_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(full_path)


@app.get("/")
def root():
    return {"message": "Argi API is running"}   


@app.get("/health")
def health_check():
    return {"status": "healthy"}
