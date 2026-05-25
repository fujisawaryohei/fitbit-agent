from fastapi import APIRouter

from app.controllers.auth import router as auth_router
from app.controllers.chat import router as chat_router
from app.controllers.health import router as health_router

router = APIRouter()
router.include_router(health_router)
router.include_router(chat_router)
router.include_router(auth_router)
