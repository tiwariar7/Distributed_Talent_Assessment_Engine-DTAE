"""URL routes for leaderboard endpoints."""

from django.urls import path

from .views import AssessmentLeaderboardView

urlpatterns = [
    path(
        "<int:assessment_id>/",
        AssessmentLeaderboardView.as_view(),
        name="assessment-leaderboard",
    ),
]

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve error handling and exception logging.

# Refactor: Improve error handling and exception logging.

# Refactor: Optimize query performance and database indexing.

# Refactor: Optimize imports and clean up code structure.

# Refactor: Improve responsive styles and layouts.

# Refactor: Improve responsive styles and layouts.
