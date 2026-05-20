import os

from dotenv import load_dotenv
from langfuse.callback import CallbackHandler  # type: ignore[import-not-found]

load_dotenv()


def get_langfuse_handler() -> CallbackHandler:
    return CallbackHandler(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
        host=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
    )
