from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    BACKEND_CORS_ORIGINS: str = '["http://localhost:5173"]'
    ANTHROPIC_API_KEY: str = "",
    CWA_API_KEY: str = ""
    UPLOAD_DIR: str = "./uploads"
    MCP_POOL_SIZE: int = 10
    GOOGLE_CLIENT_ID: str = ""
    ADMIN_EMAILS: str = '[]'

    class Config:
        env_file = ".env"

    @property
    def cors_origins(self) -> List[str]:
        """處理 JSON 格式的 CORS origins"""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return json.loads(self.BACKEND_CORS_ORIGINS)
        return self.BACKEND_CORS_ORIGINS

    @property
    def admin_emails_list(self) -> List[str]:
        """處理 JSON 格式的管理員 Email 列表"""
        if isinstance(self.ADMIN_EMAILS, str):
            return json.loads(self.ADMIN_EMAILS)
        return self.ADMIN_EMAILS


settings = Settings()
