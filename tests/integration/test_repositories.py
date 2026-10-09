from datetime import datetime, timedelta, timezone

import psycopg2
import psycopg2.errors
import psycopg2.extensions
import pytest

from backend.models.chat import Chat
from backend.models.message import Message
from backend.models.message_role import MessageRole
from backend.models.user import User
from backend.repositories.chat_repository import ChatRepository
from backend.repositories.message_repository import MessageRepository
from backend.repositories.user_repository import UserRepository

JST = timezone(timedelta(hours=9))


def make_user(fitbit_user_id: str = "ABC123", **overrides: object) -> User:
    fields: dict[str, object] = {
        "fitbit_user_id": fitbit_user_id,
        "access_token": "access-1",
        "refresh_token": "refresh-1",
        "token_expires_at": datetime(2030, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
        "scope": "activity heartrate",
    }
    fields.update(overrides)
    return User(**fields)  # type: ignore[arg-type]


def count_rows(conn: psycopg2.extensions.connection, table: str) -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        row = cur.fetchone()
    assert row is not None
    return int(row[0])


def create_user(conn: psycopg2.extensions.connection, fitbit_user_id: str = "ABC123") -> int:
    repo = UserRepository(conn)
    repo.upsert(make_user(fitbit_user_id))
    found = repo.find_by_fitbit_user_id(fitbit_user_id)
    assert found is not None and found.id is not None
    return found.id


class TestUserRepository:
    def test_upsert_then_find_returns_same_values(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        repo = UserRepository(conn)

        repo.upsert(make_user())
        found = repo.find_by_fitbit_user_id("ABC123")

        assert found is not None
        assert found.id is not None
        assert found.fitbit_user_id == "ABC123"
        assert found.access_token == "access-1"
        assert found.refresh_token == "refresh-1"
        assert found.scope == "activity heartrate"
        assert found.token_expires_at == datetime(2030, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        assert found.created_at is not None and found.updated_at is not None

    def test_find_unknown_user_returns_none(self, conn: psycopg2.extensions.connection) -> None:
        assert UserRepository(conn).find_by_fitbit_user_id("nobody") is None

    def test_second_upsert_updates_instead_of_inserting(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        repo = UserRepository(conn)
        repo.upsert(make_user())
        first = repo.find_by_fitbit_user_id("ABC123")
        assert first is not None

        repo.upsert(
            make_user(
                access_token="access-2",
                refresh_token="refresh-2",
                scope="sleep",
                token_expires_at=datetime(2031, 5, 6, 7, 8, 9, tzinfo=timezone.utc),
            )
        )
        second = repo.find_by_fitbit_user_id("ABC123")

        assert count_rows(conn, "users") == 1
        assert second is not None and first.updated_at is not None
        assert second.id == first.id
        assert second.access_token == "access-2"
        assert second.refresh_token == "refresh-2"
        assert second.scope == "sleep"
        assert second.token_expires_at == datetime(2031, 5, 6, 7, 8, 9, tzinfo=timezone.utc)
        assert second.created_at == first.created_at
        assert second.updated_at is not None and second.updated_at > first.updated_at

    def test_update_tokens_changes_only_tokens_of_that_user(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        repo = UserRepository(conn)
        repo.upsert(make_user("ABC123"))
        repo.upsert(make_user("OTHER"))
        before = repo.find_by_fitbit_user_id("ABC123")
        assert before is not None and before.updated_at is not None
        new_expiry = datetime(2032, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        repo.update_tokens("ABC123", "access-new", "refresh-new", new_expiry)
        after = repo.find_by_fitbit_user_id("ABC123")
        other = repo.find_by_fitbit_user_id("OTHER")

        assert after is not None and after.updated_at is not None
        assert after.access_token == "access-new"
        assert after.refresh_token == "refresh-new"
        assert after.token_expires_at == new_expiry
        assert after.scope == before.scope
        assert after.updated_at > before.updated_at
        assert other is not None and other.access_token == "access-1"

    def test_timezone_aware_datetime_round_trips_as_same_instant(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        repo = UserRepository(conn)
        expires = datetime(2030, 6, 1, 12, 30, 0, tzinfo=JST)

        repo.upsert(make_user(token_expires_at=expires))
        found = repo.find_by_fitbit_user_id("ABC123")

        assert found is not None
        assert found.token_expires_at.utcoffset() is not None
        assert found.token_expires_at == expires
        assert found.token_expires_at.astimezone(timezone.utc).hour == 3


class TestChatRepository:
    def test_insert_returns_id_and_find_returns_same_values(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        user_id = create_user(conn)
        repo = ChatRepository(conn)

        chat_id = repo.insert(Chat(user_id=user_id, title="睡眠について"))
        found = repo.find_by_id(chat_id)

        assert found is not None
        assert found.id == chat_id
        assert found.user_id == user_id
        assert found.title == "睡眠について"
        assert found.created_at is not None and found.updated_at is not None
        assert found.created_at.utcoffset() is not None

    def test_find_unknown_chat_returns_none(self, conn: psycopg2.extensions.connection) -> None:
        assert ChatRepository(conn).find_by_id(9999) is None

    def test_get_all_returns_only_chats_of_that_user(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        alice = create_user(conn, "ALICE")
        bob = create_user(conn, "BOB")
        repo = ChatRepository(conn)
        a1 = repo.insert(Chat(user_id=alice, title="a1"))
        a2 = repo.insert(Chat(user_id=alice, title="a2"))
        repo.insert(Chat(user_id=bob, title="b1"))

        chats = repo.get_all(alice)

        # 既知の問題: get_all に ORDER BY が無いため、並び順は保証されていない（集合で比べる）
        assert {c.id for c in chats} == {a1, a2}
        assert {c.title for c in chats} == {"a1", "a2"}
        assert all(c.user_id == alice for c in chats)
        assert repo.get_all(9999) == []

    def test_delete_by_id_removes_only_that_chat(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        user_id = create_user(conn)
        repo = ChatRepository(conn)
        keep = repo.insert(Chat(user_id=user_id, title="keep"))
        drop = repo.insert(Chat(user_id=user_id, title="drop"))

        repo.delete_by_id(drop)

        assert repo.find_by_id(drop) is None
        assert repo.find_by_id(keep) is not None

    def test_delete_unknown_chat_is_noop(self, conn: psycopg2.extensions.connection) -> None:
        user_id = create_user(conn)
        repo = ChatRepository(conn)
        chat_id = repo.insert(Chat(user_id=user_id, title="keep"))

        repo.delete_by_id(9999)

        assert repo.find_by_id(chat_id) is not None

    def test_insert_with_unknown_user_violates_foreign_key(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        with pytest.raises(psycopg2.errors.ForeignKeyViolation):
            ChatRepository(conn).insert(Chat(user_id=9999, title="orphan"))
        conn.rollback()

        assert count_rows(conn, "chats") == 0

    def test_deleting_user_cascades_to_chats_and_messages(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        user_id = create_user(conn)
        chat_id = ChatRepository(conn).insert(Chat(user_id=user_id, title="t"))
        MessageRepository(conn).insert(
            Message(chat_id=chat_id, role=MessageRole.USER, content="hi")
        )

        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", [user_id])
        conn.commit()

        assert count_rows(conn, "chats") == 0
        assert count_rows(conn, "messages") == 0

    def test_deleting_chat_cascades_to_its_messages_only(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        user_id = create_user(conn)
        chats = ChatRepository(conn)
        messages = MessageRepository(conn)
        drop = chats.insert(Chat(user_id=user_id, title="drop"))
        keep = chats.insert(Chat(user_id=user_id, title="keep"))
        messages.insert(Message(chat_id=drop, role=MessageRole.USER, content="gone"))
        messages.insert(Message(chat_id=keep, role=MessageRole.USER, content="stay"))

        chats.delete_by_id(drop)

        assert messages.get_all(drop) == []
        assert [m.content for m in messages.get_all(keep)] == ["stay"]


class TestMessageRepository:
    def test_insert_then_get_all_returns_same_values(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        chat_id = ChatRepository(conn).insert(Chat(user_id=create_user(conn), title="t"))
        repo = MessageRepository(conn)

        repo.insert(Message(chat_id=chat_id, role=MessageRole.USER, content="こんにちは"))
        result = repo.get_all(chat_id)

        assert len(result) == 1
        assert result[0].id is not None
        assert result[0].chat_id == chat_id
        assert result[0].role == MessageRole.USER
        assert result[0].content == "こんにちは"
        assert result[0].created_at is not None
        assert result[0].created_at.utcoffset() is not None

    def test_get_all_is_ordered_by_created_at_ascending(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        chat_id = ChatRepository(conn).insert(Chat(user_id=create_user(conn), title="t"))
        repo = MessageRepository(conn)

        repo.insert(Message(chat_id=chat_id, role=MessageRole.USER, content="first"))
        repo.insert(Message(chat_id=chat_id, role=MessageRole.ASSISTANT, content="second"))
        repo.insert(Message(chat_id=chat_id, role=MessageRole.USER, content="third"))
        result = repo.get_all(chat_id)

        assert [m.content for m in result] == ["first", "second", "third"]
        assert [m.role for m in result] == [
            MessageRole.USER,
            MessageRole.ASSISTANT,
            MessageRole.USER,
        ]

    def test_get_all_returns_only_messages_of_that_chat(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        user_id = create_user(conn)
        chats = ChatRepository(conn)
        one = chats.insert(Chat(user_id=user_id, title="one"))
        two = chats.insert(Chat(user_id=user_id, title="two"))
        repo = MessageRepository(conn)
        repo.insert(Message(chat_id=one, role=MessageRole.USER, content="in one"))
        repo.insert(Message(chat_id=two, role=MessageRole.USER, content="in two"))

        assert [m.content for m in repo.get_all(one)] == ["in one"]
        assert repo.get_all(9999) == []

    def test_insert_with_unknown_chat_violates_foreign_key(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        with pytest.raises(psycopg2.errors.ForeignKeyViolation):
            MessageRepository(conn).insert(
                Message(chat_id=9999, role=MessageRole.USER, content="orphan")
            )
        conn.rollback()

        assert count_rows(conn, "messages") == 0
