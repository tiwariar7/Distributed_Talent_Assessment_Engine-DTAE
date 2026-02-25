"""WebSocket URL routing for execution streaming."""

from django.urls import path

from .consumers import SubmissionExecutionConsumer

websocket_urlpatterns = [
    path(
        "ws/submissions/<int:submission_id>/",
        SubmissionExecutionConsumer.as_asgi(),
    ),
]

# Refactor: Optimize imports and clean up code structure.
