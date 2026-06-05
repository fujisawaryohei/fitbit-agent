import logging
import re
from collections.abc import Callable
from functools import wraps

_masked_params: set[str] = set()


def masked_credentials(*params: str) -> Callable:
    """指定したクエリパラメータ値をアクセスログでマスクするデコレーター。

    Usage:
        @router.get("/callback")
        @masked_credentials("code", "state")
        def callback(code: str, state: str): ...
    """
    def decorator(func: Callable) -> Callable:
        _masked_params.update(params)

        @wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
            return func(*args, **kwargs)

        return wrapper
    return decorator


class _MaskedCredentialsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not _masked_params:
            return True
        pattern = re.compile(
            r"([?&](?:" + "|".join(re.escape(p) for p in _masked_params) + r")=)[^&\s\"']+"
        )
        if isinstance(record.args, tuple):
            record.args = tuple(
                pattern.sub(r"\g<1>***", arg) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True


def setup_access_log_masking() -> None:
    """server.py 起動時に呼び出してフィルターを有効化する。"""
    logging.getLogger("uvicorn.access").addFilter(_MaskedCredentialsFilter())
