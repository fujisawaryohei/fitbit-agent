import logging

import pytest

from backend.decorators.masked_credentials import (
    _MaskedCredentialsFilter,
    _masked_params,
    masked_credentials,
    setup_access_log_masking,
)


@pytest.fixture(autouse=True)
def reset_masked_params():
    """各テスト前後に _masked_params をリセットする。"""
    _masked_params.clear()
    yield
    _masked_params.clear()


def _make_record(args: tuple) -> logging.LogRecord:
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='%s - "%s %s HTTP/%s" %d',
        args=args,
        exc_info=None,
    )
    return record


class TestMaskedCredentialsDecorator:
    def test_registers_params(self):
        @masked_credentials("code", "state")
        def dummy():
            pass

        assert "code" in _masked_params
        assert "state" in _masked_params

    def test_preserves_function_name(self):
        @masked_credentials("code")
        def my_endpoint():
            pass

        assert my_endpoint.__name__ == "my_endpoint"

    def test_preserves_return_value(self):
        @masked_credentials("code")
        def greet():
            return "hello"

        assert greet() == "hello"

    def test_multiple_decorators_accumulate_params(self):
        @masked_credentials("code")
        def endpoint_a():
            pass

        @masked_credentials("state")
        def endpoint_b():
            pass

        assert "code" in _masked_params
        assert "state" in _masked_params


class TestMaskedCredentialsFilter:
    def setup_method(self):
        self.f = _MaskedCredentialsFilter()

    def test_masks_single_param_with_question_mark(self):
        _masked_params.add("code")
        record = _make_record(
            ("127.0.0.1", "GET", "/auth/callback?code=abc123", "1.1", 302)
        )
        self.f.filter(record)
        assert record.args[2] == "/auth/callback?code=***"  # type: ignore[index]

    def test_masks_multiple_params(self):
        _masked_params.update({"code", "state"})
        record = _make_record(
            ("127.0.0.1", "GET", "/auth/callback?code=abc123&state=xyz789", "1.1", 302)
        )
        self.f.filter(record)
        assert record.args[2] == "/auth/callback?code=***&state=***"  # type: ignore[index]

    def test_does_not_mask_unregistered_params(self):
        _masked_params.add("code")
        record = _make_record(
            ("127.0.0.1", "GET", "/auth/callback?code=abc123&foo=bar", "1.1", 302)
        )
        self.f.filter(record)
        assert record.args[2] == "/auth/callback?code=***&foo=bar"  # type: ignore[index]

    def test_masks_param_in_middle_of_query(self):
        _masked_params.add("state")
        record = _make_record(
            ("127.0.0.1", "GET", "/callback?foo=1&state=secret&bar=2", "1.1", 302)
        )
        self.f.filter(record)
        assert record.args[2] == "/callback?foo=1&state=***&bar=2"  # type: ignore[index]

    def test_no_masking_when_params_empty(self):
        original = "/auth/callback?code=abc123&state=xyz"
        record = _make_record(("127.0.0.1", "GET", original, "1.1", 302))
        self.f.filter(record)
        assert record.args[2] == original  # type: ignore[index]

    def test_non_string_args_are_unchanged(self):
        _masked_params.add("code")
        record = _make_record(
            ("127.0.0.1", "GET", "/auth/callback?code=abc123", "1.1", 302)
        )
        self.f.filter(record)
        # ステータスコード（int）は変更されない
        assert record.args[4] == 302  # type: ignore[index]

    def test_always_returns_true(self):
        _masked_params.add("code")
        record = _make_record(("127.0.0.1", "GET", "/path?code=abc", "1.1", 200))
        assert self.f.filter(record) is True

    def test_no_match_leaves_args_unchanged(self):
        _masked_params.add("code")
        original = "/health"
        record = _make_record(("127.0.0.1", "GET", original, "1.1", 200))
        self.f.filter(record)
        assert record.args[2] == original  # type: ignore[index]


class TestSetupAccessLogMasking:
    def test_adds_filter_to_uvicorn_access_logger(self):
        logger = logging.getLogger("uvicorn.access")
        before = len(logger.filters)
        setup_access_log_masking()
        assert len(logger.filters) == before + 1
        # 後始末
        logger.filters = logger.filters[:before]
