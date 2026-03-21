import json
import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from .auth import get_current_user
from ..schemas.ai import QueryRequest, QueryResponse, ToolsResponse
from ..services.ai import mcp_client, save_chat_log

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.post("/query", response_model=QueryResponse)
async def query_ai(request: QueryRequest, user=Depends(get_current_user)):
    """向 AI 發送查詢並獲取回應"""
    try:
        response, tool_usages = await mcp_client.process_query(request.query, request.session_id, request.images or None)

        # 儲存對話紀錄
        images_json = None
        if request.images:
            images_json = json.dumps(
                [{"data": img.data, "media_type": img.media_type} for img in request.images],
                ensure_ascii=False,
            )
        save_chat_log(user.id, request.session_id, "user", request.query, images_json=images_json)
        tool_calls_json = None
        if tool_usages:
            tool_calls_json = json.dumps(
                [{"name": t.tool_name, "args": t.tool_args, "output": t.tool_output} for t in tool_usages],
                ensure_ascii=False,
            )
        save_chat_log(user.id, request.session_id, "assistant", response, tool_calls_json=tool_calls_json)

        return QueryResponse(response=response, session_id=request.session_id, tool_used=tool_usages)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"AI query failed: {e}")
        raise HTTPException(status_code=500, detail="AI 查詢失敗，請稍後再試")


@router.post("/stream")
async def stream_ai(request: QueryRequest, user=Depends(get_current_user)):
    """向 AI 發送查詢並以 SSE 串流回應"""
    async def event_generator():
        full_response = ""
        all_tool_calls = []
        try:
            async for event in mcp_client.process_query_stream(request.query, request.session_id, request.images or None):
                # 攔截事件累積完整回應
                if event.startswith("event: text_delta\n"):
                    data_line = event.split("data: ", 1)[1].split("\n")[0]
                    data = json.loads(data_line)
                    full_response += data.get("content", "")
                elif event.startswith("event: done\n"):
                    data_line = event.split("data: ", 1)[1].split("\n")[0]
                    data = json.loads(data_line)
                    all_tool_calls = data.get("tool_calls", [])
                yield event
        except RuntimeError as e:
            logger.error(f"AI stream failed (service unavailable): {e}")
            yield f"event: error\ndata: {json.dumps({'message': str(e)}, ensure_ascii=False)}\n\n"
            return
        except Exception as e:
            logger.error(f"AI stream failed: {e}")
            yield f"event: error\ndata: {json.dumps({'message': 'AI 查詢失敗，請稍後再試'}, ensure_ascii=False)}\n\n"
            return

        # 儲存對話紀錄
        images_json = None
        if request.images:
            images_json = json.dumps(
                [{"data": img.data, "media_type": img.media_type} for img in request.images],
                ensure_ascii=False,
            )
        save_chat_log(user.id, request.session_id, "user", request.query, images_json=images_json)
        tool_calls_json = json.dumps(all_tool_calls, ensure_ascii=False) if all_tool_calls else None
        save_chat_log(user.id, request.session_id, "assistant", full_response, tool_calls_json=tool_calls_json)

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
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Get tools failed: {e}")
        raise HTTPException(status_code=500, detail="無法取得工具列表")
