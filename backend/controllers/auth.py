import os

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse

from backend.containers import Container
from backend.services.fitbit_service import FitbitService, InvalidStateError, StateExpiredError

_FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

router = APIRouter()


@router.get("/auth/fitbit")
@inject
def authorization_url(
    fitbit_service: FitbitService = Depends(Provide[Container.fitbit_service]),
) -> RedirectResponse:
    url, _ = fitbit_service.get_authorization_url()
    if url is None:
        raise HTTPException(status_code=500, detail="URLの発行に失敗しました")
    return RedirectResponse(url)


@router.get("/auth/fitbit/callback")
@inject
def callback(
    code: str | None = None,
    state: str | None = None,
    fitbit_service: FitbitService = Depends(Provide[Container.fitbit_service]),
) -> RedirectResponse:
    try:
        user = fitbit_service.exchange_code_for_token(code, state)
        redirect = RedirectResponse(url=_FRONTEND_URL, status_code=302)
        redirect.set_cookie(key="fitbit_user_id", value=user.fitbit_user_id, httponly=True, samesite="lax")
        redirect.set_cookie(key="fitbit_connected", value="true", httponly=False, samesite="lax")
        return redirect
    except InvalidStateError:
        raise HTTPException(status_code=400, detail="不正なリクエストです")
    except StateExpiredError:
        raise HTTPException(status_code=400, detail="認証がタイムアウトしました。再度お試しください。")
