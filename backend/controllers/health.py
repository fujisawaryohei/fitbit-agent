from fastapi import APIRouter

from backend.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")
