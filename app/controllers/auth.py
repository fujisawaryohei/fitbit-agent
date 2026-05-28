import os

from fastapi import APIRouter, Response
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse

from agent.fitbit.client import FitbitClient
from app.config.connection_pool import get_connection
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthCallbackResponse
from app.services.fitbit_service import FitbitService, InvalidStateError, StateExpiredError

router = APIRouter()

_fitbit_service: FitbitService | None = None


def _get_service() -> FitbitService:
    global _fitbit_service

    if _fitbit_service is None:
        conn = get_connection()
        fitbit_client = FitbitClient(
            client_id=os.getenv("FITBIT_CLIENT_ID"),
            client_secret=os.getenv("FITBIT_CLIENT_SECRET"),
            redirect_uri=os.getenv(
                "FITBIT_REDIRECT_URI", "http://localhost:8000/auth/fitbit/callback"
            ),
        )
        user_repository = UserRepository(conn)
        _fitbit_service = FitbitService(fitbit_client, user_repository)
    return _fitbit_service


@router.get("/auth/fitbit")
def authorization_url():
    fitbit_service = _get_service()
    url, _ = fitbit_service.get_authorization_url()

    if url is None:
        raise HTTPException(status_code=500, detail="URLの発行に失敗しました")
    return RedirectResponse(url)


@router.get("/auth/fitbit/callback")
def callback(response: Response, code: str | None = None, state: str | None = None):
    fitbit_service = _get_service()
    try:
        user = fitbit_service.exchange_code_for_token(code, state)
        response.set_cookie(key="fitbit_user_id", value=user.fitbit_user_id, httponly=True, samesite="lax")
        return AuthCallbackResponse(fitbit_user_id=user.fitbit_user_id, scope=user.scope)
    except InvalidStateError:
        raise HTTPException(status_code=400, detail="不正なリクエストです")
    except StateExpiredError:
        raise HTTPException(
            status_code=400, detail="認証がタイムアウトしました。再度お試しください。"
        )
