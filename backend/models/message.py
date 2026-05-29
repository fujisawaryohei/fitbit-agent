from datetime import datetime

from backend.models.message_role import MessageRole


class Message:
    def __init__(
        self,
        chat_id: int,
        role: MessageRole,
        content: str,
        id: int | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.chat_id = chat_id
        self.role = role
        self.content = content
        self.created_at = created_at
