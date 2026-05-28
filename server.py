from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import router

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
