from typing import Literal

from pydantic import BaseModel, field_validator


class ChatRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("messageを空文字列にすることはできません")
        if len(v) > 2000:
            raise ValueError("messageは2000文字以内で入力してください")
        return v


class SSEChunk(BaseModel):
    type: Literal["chunk", "done", "error"]
    content: str = ""
    session_id: str = ""
