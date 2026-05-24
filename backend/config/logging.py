"""
Structured logging configuration for production observability.

Emits JSON logs when ``LOG_FORMAT=json``; human-readable logs in development.
"""

from __future__ import annotations

import logging


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, self.datefmt),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in payload:
                continue
            if key in ("msg", "args", "levelno", "levelname", "pathname", "lineno"):
                continue
            if key in ("submission_id", "problem_id", "assessment_id", "user_id"):
                payload[key] = value
        return json.dumps(payload)


def build_logging_config(log_level: str, log_format: str) -> dict:
    """Build Django ``LOGGING`` dict from environment-driven options."""
    use_json = log_format.lower() == "json"
    formatter_name = "json" if use_json else "verbose"

    formatters = {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
        "json": {
            "()": "config.logging.JsonFormatter",
        },
    }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": formatter_name,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
        "loggers": {
            "django": {"level": "INFO", "propagate": True},
            "django.request": {"level": "WARNING", "propagate": True},
            "celery": {"level": "INFO", "propagate": True},
            "apps": {"level": log_level, "propagate": True},
            "infrastructure": {"level": log_level, "propagate": True},
        },
    }
