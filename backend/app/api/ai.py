from contextlib import AsyncExitStack
from typing import Optional
import os
import json

from anthropic import Anthropic, AsyncAnthropic
from dotenv import load_dotenv

# 載入 .env 環境變數
load_dotenv()
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from mcp import ClientSession, StdioServerParameters
from .auth import get_current_user
from mcp.client.stdio import stdio_client
from pydantic import BaseModel

# Claude 模型常數
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

# 取得 server.py 的絕對路徑
SERVER_PATH = os.path.join(os.path.dirname(__file__), "..", "mcp_server", "server.py")


class QueryRequest(BaseModel):
    """查詢請求模型"""
    query: str
    session_id: str


class ToolUsage(BaseModel):
    """工具使用資訊"""
    tool_name: str
    tool_args: dict
    tool_output: Optional[str] = None


class QueryResponse(BaseModel):
    """查詢回應模型"""
    response: str
    session_id: str
    tool_used: list[ToolUsage] = []


class Tool(BaseModel):
    """工具資訊模型"""
    name: str
    description: str


class ToolsResponse(BaseModel):
    """工具列表回應模型"""
    tools: list[Tool]


class MCPClient:
    """MCP 客戶端類別，負責連接 MCP 服務器並與 Claude AI 互動"""

    def __init__(self):
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        self.conversations = {}  # {session_id: history}

    async def connect_to_server(self):
        """連接到 MCP 服務器（server.py）"""
        server_params = StdioServerParameters(
            command="python",
            args=[SERVER_PATH],
            env=os.environ.copy(),
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport

        self.session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
        await self.session.initialize()

    async def get_tools(self) -> list[dict]:
        """獲取可用的工具列表"""
        response = await self.session.list_tools()
        return [{"name": tool.name, "description": tool.description} for tool in response.tools]

    async def process_query(self, query: str, session_id: str) -> tuple[str, list[ToolUsage]]:
        """處理用戶查詢，使用 Claude 和可用工具"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        conversation_history = self.conversations[session_id]
        conversation_history.append({"role": "user", "content": query})

        response = await self.session.list_tools()
        available_tools = [
            {"name": tool.name, "description": tool.description, "input_schema": tool.inputSchema}
            for tool in response.tools
        ]

        all_tool_usages = []
        final_text = ""

        while True:
            response = self.anthropic.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=4096,
                system="請使用繁體中文回答用戶問題",
                messages=conversation_history,
                tools=available_tools
            )

            assistant_content = []
            tool_results = []
            has_tool_use = False

            for content in response.content:
                assistant_content.append(content)

                if content.type == "tool_use":
                    has_tool_use = True
                    tool_name = content.name
                    tool_args = content.input

                    result = await self.session.call_tool(tool_name, tool_args)

                    # 提取工具回傳的文字內容
                    output_text = ""
                    if result.content:
                        for item in result.content:
                            if hasattr(item, "text"):
                                output_text += item.text
                            else:
                                output_text += str(item)
                    
                    all_tool_usages.append(ToolUsage(
                        tool_name=tool_name, 
                        tool_args=tool_args,
                        tool_output=output_text
                    ))

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": output_text
                    })

            conversation_history.append({"role": "assistant", "content": assistant_content})

            if has_tool_use:
                conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })
            else:
                # 沒有工具調用，這是最終回應
                text_blocks = [c.text for c in response.content if c.type == "text"]
                final_text = "\n".join(text_blocks)
                break

        return final_text, all_tool_usages

    async def process_query_stream(self, query: str, session_id: str):
        """處理用戶查詢（串流模式），使用 async generator yield SSE 事件"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        conversation_history = self.conversations[session_id]
        conversation_history.append({"role": "user", "content": query})

        response = await self.session.list_tools()
        available_tools = [
            {"name": tool.name, "description": tool.description, "input_schema": tool.inputSchema}
            for tool in response.tools
        ]

        async_client = AsyncAnthropic()
        all_tool_usages = []

        while True:
            # 使用串流 API 呼叫 Claude
            async with async_client.messages.stream(
                model=ANTHROPIC_MODEL,
                max_tokens=4096,
                system="請使用繁體中文回答用戶問題",
                messages=conversation_history,
                tools=available_tools,
            ) as stream:
                async for event in stream:
                    if event.type == "text":
                        yield f"event: text_delta\ndata: {json.dumps({'content': event.text}, ensure_ascii=False)}\n\n"

                final_message = await stream.get_final_message()

            # 將助手回應加入對話歷史
            conversation_history.append({"role": "assistant", "content": list(final_message.content)})

            tool_uses = [c for c in final_message.content if c.type == "tool_use"]

            if not tool_uses:
                break

            # 執行工具
            tool_results = []
            for tu in tool_uses:
                yield f"event: tool_start\ndata: {json.dumps({'name': tu.name, 'args': tu.input}, ensure_ascii=False)}\n\n"

                result = await self.session.call_tool(tu.name, tu.input)
                output_text = ""
                if result.content:
                    for item in result.content:
                        if hasattr(item, "text"):
                            output_text += item.text
                        else:
                            output_text += str(item)

                yield f"event: tool_end\ndata: {json.dumps({'name': tu.name, 'output': output_text}, ensure_ascii=False)}\n\n"

                all_tool_usages.append(ToolUsage(
                    tool_name=tu.name,
                    tool_args=tu.input,
                    tool_output=output_text,
                ))

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": output_text,
                })

            conversation_history.append({"role": "user", "content": tool_results})

        # 完成
        done_data = {
            "tool_calls": [
                {"name": t.tool_name, "args": t.tool_args, "output": t.tool_output}
                for t in all_tool_usages
            ]
        }
        yield f"event: done\ndata: {json.dumps(done_data, ensure_ascii=False)}\n\n"

    async def cleanup(self):
        """清理資源並關閉連接"""
        await self.exit_stack.aclose()


# 全域 MCP 客戶端實例
mcp_client = MCPClient()

# 建立路由
router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.post("/query", response_model=QueryResponse)
async def query_ai(request: QueryRequest, _user=Depends(get_current_user)):
    """向 AI 發送查詢並獲取回應"""
    try:
        response, tool_usages = await mcp_client.process_query(request.query, request.session_id)
        return QueryResponse(response=response, session_id=request.session_id, tool_used=tool_usages)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"AI query failed: {e}")
        raise HTTPException(status_code=500, detail="AI 查詢失敗，請稍後再試")


@router.post("/stream")
async def stream_ai(request: QueryRequest, _user=Depends(get_current_user)):
    """向 AI 發送查詢並以 SSE 串流回應"""
    async def event_generator():
        try:
            async for event in mcp_client.process_query_stream(request.query, request.session_id):
                yield event
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"AI stream failed: {e}")
            yield f"event: error\ndata: {json.dumps({'message': 'AI 查詢失敗，請稍後再試'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/tools", response_model=ToolsResponse)
async def get_tools(_user=Depends(get_current_user)):
    """獲取目前可用的工具列表"""
    try:
        tools = await mcp_client.get_tools()
        return ToolsResponse(tools=tools)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Get tools failed: {e}")
        raise HTTPException(status_code=500, detail="無法取得工具列表")
