from fastapi import APIRouter

from api.chat import router as chat_router
from api.health import router as health_router

router = APIRouter()
router.include_router(health_router)
router.include_router(chat_router)
