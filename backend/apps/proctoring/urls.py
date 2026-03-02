from django.urls import path
from .views import (
    StartProctoringSessionView,
    ReportViolationView,
    ProctoringStatusView,
    EndProctoringSessionView,
)

urlpatterns = [
    path("session/start/", StartProctoringSessionView.as_view(), name="proctoring-session-start"),
    path("session/end/", EndProctoringSessionView.as_view(), name="proctoring-session-end"),
    path("session/violation/", ReportViolationView.as_view(), name="proctoring-report-violation"),
    path("session/<int:pk>/", ProctoringStatusView.as_view(), name="proctoring-session-detail"),
]

# Refactor: Update validation checks and constraints.

# Refactor: Improve responsive styles and layouts.
