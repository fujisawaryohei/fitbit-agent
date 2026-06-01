import os
from collections.abc import Generator

import psycopg2.extensions
from dependency_injector import containers, providers

from agent.fitbit.client import FitbitClient
from backend.config.connection_pool import get_connection, release_connection
from backend.repositories.chat_repository import ChatRepository
from backend.repositories.message_repository import MessageRepository
from backend.repositories.user_repository import UserRepository
from backend.services.fitbit_service import FitbitService


def _create_conn() -> Generator[psycopg2.extensions.connection, None, None]:
    conn = get_connection()
    try:
        yield conn
    finally:
        release_connection(conn)


def _create_fitbit_client() -> FitbitClient:
    return FitbitClient(
        client_id=os.getenv("FITBIT_CLIENT_ID", ""),
        client_secret=os.getenv("FITBIT_CLIENT_SECRET", ""),
        redirect_uri=os.getenv("FITBIT_REDIRECT_URI", "http://localhost:8000/auth/fitbit/callback"),
    )


class Container(containers.DeclarativeContainer):
    pass

    conn = providers.Resource(_create_conn)

    user_repo = providers.Factory(UserRepository, conn=conn)
    chat_repo = providers.Factory(ChatRepository, conn=conn)
    message_repo = providers.Factory(MessageRepository, conn=conn)

    fitbit_client = providers.Singleton(_create_fitbit_client)
    fitbit_service = providers.Singleton(FitbitService, fitbit_client=fitbit_client, user_repository=user_repo)
