from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.containers import Container
from backend.decorators.masked_credentials import setup_access_log_masking
from backend.router import router

setup_access_log_masking()

container = Container()
container.wire(modules=["backend.controllers.auth", "backend.controllers.chat"])

app = FastAPI(title="Fitbit Agent API", version="1.0")

_cors_origins = ["http://localhost:3000"]
if _extra := __import__("os").getenv("CORS_ORIGINS"):
    _cors_origins += [o.strip() for o in _extra.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
