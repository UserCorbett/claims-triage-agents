"""Structured JSON logging for the triage pipeline.

Each ``logging.LogRecord`` is emitted as a single-line JSON object containing
``timestamp``, ``level``, ``event`` (the log message) and any extra fields
passed through the ``extra=`` argument of the log call. Suitable for shipping
to CloudWatch, Datadog, or any log aggregator that expects one JSON document
per line.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone

_RESERVED_LOG_RECORD_ATTRS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName", "message", "asctime",
}


class JsonFormatter(logging.Formatter):
    """Format LogRecords as single-line JSON objects.

    The output schema is: timestamp (ISO-8601 UTC), level, event (the format
    string after % substitution), plus every key passed via ``extra=`` —
    e.g. ``agent_name``, ``tokens_in``, ``duration_ms``.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_ATTRS:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> logging.Logger:
    """Wire the root logger to JSON-stdout output. Honours ``LOG_LEVEL`` env."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]

    logging.getLogger("httpx").setLevel(logging.WARNING)

    return root
