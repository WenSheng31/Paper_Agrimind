from typing import Optional

from pydantic import BaseModel


class ImageData(BaseModel):
    data: str  # base64 encoded
    media_type: str = "image/jpeg"  # image/jpeg, image/png, image/gif, image/webp


class QueryRequest(BaseModel):
    query: str
    session_id: str
    images: list[ImageData] = []


class ToolUsage(BaseModel):
    tool_name: str
    tool_args: dict
    tool_output: Optional[str] = None


class QueryResponse(BaseModel):
    response: str
    session_id: str
    tool_used: list[ToolUsage] = []


class Tool(BaseModel):
    name: str
    description: str


class ToolsResponse(BaseModel):
    tools: list[Tool]
