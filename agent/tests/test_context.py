from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest

from agent import context
from agent.context import get_fitbit_client, set_fitbit_client


@pytest.fixture
def unset_client() -> Iterator[None]:
    token = context._fitbit_client.set(None)
    try:
        yield
    finally:
        context._fitbit_client.reset(token)


@pytest.mark.usefixtures("unset_client")
class TestFitbitClientContext:
    def test_unset_raises_runtime_error(self) -> None:
        with pytest.raises(RuntimeError, match="認証"):
            get_fitbit_client()

    def test_set_client_is_returned(self) -> None:
        client = MagicMock()
        set_fitbit_client(client)
        assert get_fitbit_client() is client
