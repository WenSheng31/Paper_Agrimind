from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.init_db import init_db
from .api import auth, admin, agriculture, ai, knowledge

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # 啟動時連接 MCP 服務器
    await ai.mcp_client.connect_to_server()
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

# 註冊路由
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(agriculture.router)
app.include_router(ai.router)
app.include_router(knowledge.router)

@app.get("/")
def root():
    return {"message": "Argi API is running"}   


@app.get("/health")
def health_check():
    return {"status": "healthy"}
