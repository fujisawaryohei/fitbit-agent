from datetime import datetime


class Chat:
    def __init__(
        self,
        user_id: int,
        title: str,
        id: int | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.user_id = user_id
        self.title = title
        self.created_at = created_at
        self.updated_at = updated_at
