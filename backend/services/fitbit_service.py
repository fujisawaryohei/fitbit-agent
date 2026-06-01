from agent.fitbit.client import FitbitClient
from backend.models.auth import CsrfState
from backend.models.user import User
from backend.repositories.user_repository import UserRepository


class InvalidStateError(Exception):
    pass


class StateExpiredError(Exception):
    pass


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

    def exchange_code_for_token(self, code: str | None, state: str | None) -> User:
        if state not in self._state_store:
            raise InvalidStateError("不正な値です")

        csrf_state = self._state_store[state]
        if csrf_state.is_expired():
            del self._state_store[state]
            raise StateExpiredError("stateの有効期限が切れています")

        del self._state_store[state]

        if code is None:
            raise InvalidStateError("codeが指定されていません")

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
