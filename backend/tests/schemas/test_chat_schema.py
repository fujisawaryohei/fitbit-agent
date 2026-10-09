import pytest
from pydantic import ValidationError

from backend.schemas.chat import ChatRequest


class TestChatRequestValidation:
    @pytest.mark.parametrize("blank", ["", " ", "   ", "\n\t "])
    def test_blank_message_is_rejected(self, blank):
        with pytest.raises(ValidationError, match="空文字列"):
            ChatRequest(message=blank)

    def test_surrounding_whitespace_is_stripped(self):
        assert ChatRequest(message="  こんにちは \n").message == "こんにちは"

    def test_2000_chars_is_accepted(self):
        assert len(ChatRequest(message="a" * 2000).message) == 2000

    def test_2001_chars_is_rejected(self):
        with pytest.raises(ValidationError, match="2000文字以内"):
            ChatRequest(message="a" * 2001)

    def test_length_is_checked_after_stripping(self):
        assert len(ChatRequest(message=" " + "a" * 2000 + " ").message) == 2000
