import os

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from agent.context import set_fitbit_client
from agent.fitbit.client import FitbitClient
from agent.graph import get_agent
from backend.config.connection_pool import get_connection, release_connection
from backend.containers import Container
from backend.models.chat import Chat
from backend.models.message import Message
from backend.models.message_role import MessageRole
from backend.repositories.chat_repository import ChatRepository
from backend.repositories.message_repository import MessageRepository
from backend.repositories.user_repository import UserRepository
from backend.schemas.chat import ChatMessageResponse, ChatRequest, SSEChunk

router = APIRouter()
_agent = get_agent()


@router.post("/chat")
@inject
def chat(
    request: ChatRequest,
    fitbit_user_id: str | None = Cookie(default=None),
    user_repo: UserRepository = Depends(Provide[Container.user_repo]),
    chat_repo: ChatRepository = Depends(Provide[Container.chat_repo]),
) -> StreamingResponse:
    if fitbit_user_id is None:
        raise HTTPException(
            status_code=401, detail="認証が必要です。先に /auth/fitbit で認証してください。"
        )

    user = user_repo.find_by_fitbit_user_id(fitbit_user_id)

    if user is None:
        raise HTTPException(
            status_code=401, detail="ユーザーが見つかりません。再認証してください。"
        )

    if user.is_token_expired():
        raise HTTPException(
            status_code=401, detail="アクセストークンの有効期限が切れています。再認証してください。"
        )

    chat_id = chat_repo.insert(Chat(user_id=user.id, title=request.message[:50]))

    fitbit_client = FitbitClient(
        client_id=os.getenv("FITBIT_CLIENT_ID", ""),
        client_secret=os.getenv("FITBIT_CLIENT_SECRET", ""),
        access_token=user.access_token,
        refresh_token=user.refresh_token,
    )

    # _sse_generator は StreamingResponse 返却後も動き続けるため
    # conn のライフサイクルを DI に委ねず手動管理する
    conn = get_connection()
    return StreamingResponse(
        _sse_generator(
            message=request.message,
            user_id=user.id,
            chat_id=chat_id,
            conn=conn,
            fitbit_client=fitbit_client,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/chats/{chat_id}/messages")
@inject
def list_messages(
    chat_id: int,
    fitbit_user_id: str | None = Cookie(default=None),
    user_repo: UserRepository = Depends(Provide[Container.user_repo]),
    chat_repo: ChatRepository = Depends(Provide[Container.chat_repo]),
    message_repo: MessageRepository = Depends(Provide[Container.message_repo]),
) -> list[ChatMessageResponse]:
    if fitbit_user_id is None:
        raise HTTPException(
            status_code=401, detail="認証が必要です。先に /auth/fitbit で認証してください。"
        )

    user = user_repo.find_by_fitbit_user_id(fitbit_user_id)

    if user is None:
        raise HTTPException(
            status_code=401, detail="ユーザーが見つかりません。再認証してください。"
        )

    chat = chat_repo.find_by_id(chat_id)

    if chat is None or chat.user_id != user.id:
        raise HTTPException(status_code=404, detail="チャットが見つかりません。")

    messages = message_repo.list(chat_id)
    return [
        ChatMessageResponse(
            id=message.id,
            chat_id=message.chat_id,
            role=str(message.role),
            content=message.content,
            created_at=message.created_at,
        )
        for message in messages
    ]


async def _sse_generator(
    message: str,
    user_id: int,
    chat_id: int,
    conn,
    fitbit_client: FitbitClient,
):
    set_fitbit_client(fitbit_client)
    config = {"configurable": {"thread_id": str(chat_id)}}
    message_repo = MessageRepository(conn)

    message_repo.insert(Message(chat_id=chat_id, role=MessageRole.USER, content=message))

    assistant_content = ""
    try:
        async for msg, metadata in _agent.astream(
            {"messages": [HumanMessage(content=message)], "session_id": str(user_id)},
            config=config,
            stream_mode="messages",
        ):
            if metadata.get("langgraph_node") != "agent_node":
                continue

            content = msg.content
            if isinstance(content, list):
                content = "".join(
                    block.get("text", "") for block in content if isinstance(block, dict)
                )
            if content:
                assistant_content += content
                data = SSEChunk(type="chunk", content=content, session_id=str(user_id))
                yield f"data: {data.model_dump_json()}\n\n"

        if assistant_content:
            message_repo.insert(
                Message(chat_id=chat_id, role=MessageRole.ASSISTANT, content=assistant_content)
            )

        yield f"data: {SSEChunk(type='done', session_id=str(user_id)).model_dump_json()}\n\n"
    except Exception as e:
        yield f"data: {SSEChunk(type='error', content=repr(e), session_id=str(user_id)).model_dump_json()}\n\n"
    finally:
        release_connection(conn)
