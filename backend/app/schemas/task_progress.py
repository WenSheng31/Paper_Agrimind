from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaskProgressUpdate(BaseModel):
    current_step: int
    is_completed: bool = False


class TaskProgressResponse(BaseModel):
    current_step: int
    is_completed: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
