from agent.fitbit.client import FitbitClient
from app.models.auth import CsrfState
from app.models.user import User
from app.repositories.user_repository import UserRepository


class FitbitService:
    def __init__(self, fitbit_client: FitbitClient, user_repository: UserRepository) -> None:
        self._client = fitbit_client
        self._user_repository = user_repository
        self._state_store: dict[str, CsrfState] = {}

    def get_authorization_url(self) -> tuple[str, str]:
        state = CsrfState.generate()
        self._state_store[state.value] = state
        authorization_url = self._client.get_authorization_url(state.value)
        return authorization_url, state.value

    def exchange_code_for_token(self, code) -> User:
        token_response = self._client.exchange_code_for_token(code)
        user = User(
            fitbit_user_id=token_response.user_id,
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token,
            token_expires_at=token_response.expires_at(),
            scope=token_response.scope,
        )
        self._user_repository.upsert(user)
        return user

    def update_token(self) -> None:
        token_response = self._client.refresh_access_token()
        self._user_repository.update_tokens(
            fitbit_user_id=token_response.user_id,
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token,
            token_expires_at=token_response.expires_at(),
        )
