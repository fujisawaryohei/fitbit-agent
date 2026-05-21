from dotenv import load_dotenv
from langfuse.langchain import CallbackHandler  # type: ignore[import-not-found]

load_dotenv()


def get_langfuse_handler() -> CallbackHandler:
    return CallbackHandler()
