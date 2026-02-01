from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class KnowledgeDocumentCreate(BaseModel):
    title: str
    content: str


class KnowledgeDocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    source_filename: Optional[str] = None
    chunk_index: int
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeUploadResponse(BaseModel):
    title: str
    filename: Optional[str] = None
    chunk_count: int
    message: str


class KnowledgeGroupResponse(BaseModel):
    title: str
    source_filename: Optional[str] = None
    chunk_count: int
    created_at: datetime
