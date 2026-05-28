from contextvars import ContextVar

from agent.fitbit.client import FitbitClient

_fitbit_client: ContextVar[FitbitClient | None] = ContextVar("fitbit_client", default=None)


def set_fitbit_client(client: FitbitClient) -> None:
    _fitbit_client.set(client)


def get_fitbit_client() -> FitbitClient:
    client = _fitbit_client.get()
    if client is None:
        raise RuntimeError("Fitbit クライアントが設定されていません。先に /auth/fitbit で認証してください。")
    return client
