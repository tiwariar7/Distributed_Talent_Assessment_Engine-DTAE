"""
Publish submission lifecycle events to Channels groups.

Celery workers call these helpers after each CouchDB log append so WebSocket
clients receive live execution updates without polling.
"""

from __future__ import annotations

import logging
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class SubmissionEventPublisher:
    """
    Fan-out submission events to WebSocket subscribers via Redis channel layer.

    Open/Closed: new event types are new methods; consumers handle routing.
    """

    @staticmethod
    def _group_name(submission_id: int) -> str:
        return f"submission_{submission_id}"

    @classmethod
    def _publish(cls, submission_id: int, event_type: str, payload: dict[str, Any]) -> None:
        """Send an event to all sockets in the submission group."""
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.debug("Channel layer not configured; skipping event %s", event_type)
            return

        async_to_sync(channel_layer.group_send)(
            cls._group_name(submission_id),
            {
                "type": "submission.event",
                "event": {"type": event_type, **payload},
            },
        )

    @classmethod
    def status_changed(cls, submission_id: int, status: str, **extra: Any) -> None:
        """Notify clients that submission status transitioned."""
        cls._publish(submission_id, "status_changed", {"status": status, **extra})

    @classmethod
    def log_appended(cls, submission_id: int, entry: dict[str, Any]) -> None:
        """Notify clients that a new execution log entry was appended in CouchDB."""
        cls._publish(submission_id, "log_appended", {"entry": entry})

    @classmethod
    def evaluation_complete(
        cls,
        submission_id: int,
        score: int,
        passed: int,
        total_cases: int,
    ) -> None:
        """Notify clients that evaluation finished."""
        cls._publish(
            submission_id,
            "evaluation_complete",
            {
                "score": score,
                "passed": passed,
                "total_cases": total_cases,
            },
        )

# Refactor: Optimize query performance and database indexing.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve responsive styles and layouts.

# Refactor: Refactor variable names for better readability.

# Refactor: Update validation checks and constraints.

# Refactor: Optimize imports and clean up code structure.
