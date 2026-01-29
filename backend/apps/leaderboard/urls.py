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
