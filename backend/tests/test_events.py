"""Tests for real-time submission event publishing and WebSockets."""

from unittest.mock import patch
import pytest
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import AccessToken

from apps.assessments.models import Submission
from apps.executions.routing import websocket_urlpatterns
from infrastructure.events import SubmissionEventPublisher

websocket_app = URLRouter(websocket_urlpatterns)


@pytest.fixture
def queued_submission(candidate_user, problem) -> Submission:
    """Pre-created submission for WebSocket tests (sync fixture)."""
    return Submission.objects.create(
        problem=problem,
        candidate=candidate_user,
        status=Submission.Status.QUEUED,
        couchdb_source_doc_id="src_1",
        couchdb_execution_log_doc_id="log_1",
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@patch("apps.executions.consumers.DocumentRepository")
async def test_websocket_streams_published_events(
    mock_repo_class,
    candidate_user,
    queued_submission,
) -> None:
    """Authenticated candidate receives live events over WebSocket."""
    mock_repo_class.return_value.get_execution_log_entries.return_value = []

    token = str(AccessToken.for_user(candidate_user))
    submission = queued_submission

    communicator = WebsocketCommunicator(
        websocket_app,
        f"/ws/submissions/{submission.pk}/?token={token}",
    )
    connected, _ = await communicator.connect()
    assert connected

    handshake = await communicator.receive_json_from()
    assert handshake["type"] == "connected"
    assert handshake["status"] == Submission.Status.QUEUED

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"submission_{submission.pk}",
        {
            "type": "submission.event",
            "event": {
                "type": "log_appended",
                "entry": {"test_case_index": 0, "passed": True},
            },
        },
    )

    event = await communicator.receive_json_from(timeout=2)
    assert event["type"] == "log_appended"
    assert event["entry"]["passed"] is True

    await communicator.disconnect()


@pytest.fixture
def other_user(django_user_model):
    """Second user who does not own the queued submission."""
    return django_user_model.objects.create_user(
        username="other@test.com",
        email="other@test.com",
        password="testpass123",
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_websocket_rejects_unauthorized_user(
    other_user,
    queued_submission,
) -> None:
    """Users who do not own the submission cannot subscribe."""
    token = str(AccessToken.for_user(other_user))
    submission = queued_submission

    communicator = WebsocketCommunicator(
        websocket_app,
        f"/ws/submissions/{submission.pk}/?token={token}",
    )
    connected, _ = await communicator.connect()
    assert not connected

    await communicator.disconnect()


@pytest.mark.django_db
def test_event_publisher_broadcasts_without_error(candidate_user, problem) -> None:
    """Publisher sends all lifecycle events through the channel layer."""
    submission = Submission.objects.create(
        problem=problem,
        candidate=candidate_user,
        status=Submission.Status.QUEUED,
        couchdb_source_doc_id="src_1",
        couchdb_execution_log_doc_id="log_1",
    )

    SubmissionEventPublisher.status_changed(submission.pk, "running")
    SubmissionEventPublisher.log_appended(
        submission.pk,
        {"test_case_index": 0, "passed": True},
    )
    SubmissionEventPublisher.evaluation_complete(submission.pk, 100, 1, 1)

# Refactor: Improve responsive styles and layouts.

# Refactor: Improve error handling and exception logging.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve error handling and exception logging.

# Refactor: Enhance component rendering performance.

# Refactor: Update validation checks and constraints.

# Refactor: Add typing hints and documentation docstrings.
