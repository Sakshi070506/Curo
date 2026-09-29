"""
Module   : Logger
Owner    : Backend Lead
Purpose  : Structured JSON logging setup with request IDs.
"""

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

from pythonjsonlogger import jsonlogger

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    """Add request_id to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "none"
        return True


def get_logger(name: str) -> logging.Logger:
    """Get a logger with JSON formatting and request ID."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(request_id)s %(message)s",
            timestamp=True,
        )
        handler.setFormatter(formatter)
        handler.addFilter(RequestIdFilter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def set_request_id(request_id: str | None = None) -> str:
    """Set request ID for current context. Returns the ID."""
    if request_id is None:
        request_id = str(uuid.uuid4())[:8]
    request_id_var.set(request_id)
    return request_id


def clear_request_id() -> None:
    """Clear request ID from current context."""
    request_id_var.set(None)


class LogContext:
    """Context manager for structured logging with additional fields."""

    def __init__(self, logger: logging.Logger, **kwargs: Any):
        self.logger = logger
        self.kwargs = kwargs
        self.old_factory = logging.getLogRecordFactory()

    def __enter__(self):
        def record_factory(*args: Any, **kw: Any) -> logging.LogRecord:
            record = self.old_factory(*args, **kw)
            for k, v in self.kwargs.items():
                setattr(record, k, v)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, *args: Any):
        logging.setLogRecordFactory(self.old_factory)


def log_with_context(logger: logging.Logger, level: int, msg: str, **kwargs: Any) -> None:
    """Log a message with additional context fields."""
    extra = {"extra_fields": kwargs}
    logger.log(level, msg, extra=extra)
