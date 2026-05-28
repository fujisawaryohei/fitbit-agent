import os

from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from agent.context import set_fitbit_client
from agent.fitbit.client import FitbitClient
from agent.graph import get_agent
from app.config.connection_pool import get_connection
from app.repositories.user_repository import UserRepository
from app.schemas.chat import ChatRequest, SSEChunk

router = APIRouter()
_agent = get_agent()


@router.post("/chat")
def chat(
    request: ChatRequest,
    fitbit_user_id: str | None = Cookie(default=None),
) -> StreamingResponse:
    if fitbit_user_id is None:
        raise HTTPException(
            status_code=401, detail="認証が必要です。先に /auth/fitbit で認証してください。"
        )

    conn = get_connection()
    user = UserRepository(conn).find_by_fitbit_user_id(fitbit_user_id)

    if user is None:
        raise HTTPException(
            status_code=401, detail="ユーザーが見つかりません。再認証してください。"
        )

    if user.is_token_expired():
        raise HTTPException(
            status_code=401, detail="アクセストークンの有効期限が切れています。再認証してください。"
        )

    set_fitbit_client(
        FitbitClient(
            client_id=os.getenv("FITBIT_CLIENT_ID", ""),
            client_secret=os.getenv("FITBIT_CLIENT_SECRET", ""),
            access_token=user.access_token,
            refresh_token=user.refresh_token,
        )
    )

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
