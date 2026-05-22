from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from agent.graph import get_agent
from app.models.chat import ChatRequest, SSEChunk

router = APIRouter()
_agent = get_agent()


@router.post("/chat")
def chat(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _sse_generator(message=request.message, session_id=request.session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _sse_generator(message: str, session_id: str):
    config = {"configurable": {"thread_id": session_id}}
    try:
        async for msg, _ in _agent.astream(
            {"messages": [HumanMessage(content=message)], "session_id": session_id},
            config=config,
            stream_mode="messages",
        ):
            content = msg.content
            if isinstance(content, list):
                content = "".join(
                    block.get("text", "") for block in content if isinstance(block, dict)
                )
            if content:
                data = SSEChunk(type="chunk", content=content, session_id=session_id)
                yield f"data: {data.model_dump_json()}\n\n"

        yield f"data: {SSEChunk(type='done', session_id=session_id).model_dump_json()}\n\n"
    except Exception as e:
        yield f"data: {SSEChunk(type='error', content=repr(e), session_id=session_id).model_dump_json()}\n\n"
