from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    BACKEND_CORS_ORIGINS: str = '["http://localhost:5173"]'
    ANTHROPIC_API_KEY: str = "",
    CWA_API_KEY: str = ""
    UPLOAD_DIR: str = "./uploads"
    MCP_POOL_SIZE: int = 10

    class Config:
        env_file = ".env"

    @property
    def cors_origins(self) -> List[str]:
        """處理 JSON 格式的 CORS origins"""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return json.loads(self.BACKEND_CORS_ORIGINS)
        return self.BACKEND_CORS_ORIGINS


settings = Settings()
