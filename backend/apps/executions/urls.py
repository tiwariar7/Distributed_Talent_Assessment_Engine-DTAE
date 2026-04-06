"""URL routes for execution status endpoints."""

from django.urls import path

from .views import SubmissionExecutionLogView, SubmissionStatusView

urlpatterns = [
    path(
        "submissions/<int:pk>/",
        SubmissionStatusView.as_view(),
        name="submission-status",
    ),
    path(
        "submissions/<int:pk>/log/",
        SubmissionExecutionLogView.as_view(),
        name="submission-execution-log",
    ),
]

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Enhance component rendering performance.
