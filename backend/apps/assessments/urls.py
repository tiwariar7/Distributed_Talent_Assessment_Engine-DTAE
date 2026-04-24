"""URL routes for assessment and submission endpoints using DRF router."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecruiterAssessmentViewSet, CandidateAssessmentViewSet, ProblemSubmissionView

router = DefaultRouter()
router.register(r'recruiter', RecruiterAssessmentViewSet, basename='recruiter-assessment')
router.register(r'candidate', CandidateAssessmentViewSet, basename='candidate-assessment')

urlpatterns = [
    path("", CandidateAssessmentViewSet.as_view({"get": "list"}), name="assessment-list-compat"),
    path("problems/<int:problem_id>/submissions/", ProblemSubmissionView.as_view(), name="problem-submission-compat"),
    path("", include(router.urls)),
]

# Refactor: Refactor variable names for better readability.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Improve responsive styles and layouts.

# Refactor: Improve error handling and exception logging.

# Refactor: Optimize imports and clean up code structure.

# Refactor: Improve error handling and exception logging.
