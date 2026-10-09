import logging

import pytest

from backend.decorators.masked_credentials import _MaskedCredentialsFilter, _masked_params


@pytest.fixture(autouse=True)
def reset_masked_params():
    _masked_params.clear()
    yield
    _masked_params.clear()


class TestNonTupleArgs:
    def test_dict_args_are_left_untouched_and_record_is_kept(self):
        _masked_params.add("code")
        args = {"path": "/auth/callback?code=abc123"}
        record = logging.LogRecord(
            "uvicorn.access", logging.INFO, "", 0, "%(path)s", (args,), None
        )

        assert _MaskedCredentialsFilter().filter(record) is True
        assert record.args == {"path": "/auth/callback?code=abc123"}

    def test_none_args_are_left_untouched_and_record_is_kept(self):
        _masked_params.add("code")
        record = logging.LogRecord(
            "uvicorn.access", logging.INFO, "", 0, "/auth/callback?code=abc123", None, None
        )

        assert _MaskedCredentialsFilter().filter(record) is True
        assert record.args is None
