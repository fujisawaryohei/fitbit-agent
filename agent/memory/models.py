import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    """pgvector に保存される Long-term memory のレコード"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    content: str  # LLM が要約したテキスト
    embedding: list[float]  # ベクトル（pgvector に保存）
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"arbitrary_types_allowed": True}
