"""URL routes for recruiter dashboard endpoints."""

from django.urls import path

from .views import (
    RecruiterAssessmentDetailView,
    RecruiterAssessmentListCreateView,
    RecruiterAssessmentPublishView,
    RecruiterProblemCreateView,
    RecruiterProblemDetailView,
    RecruiterTestCasesUploadView,
)
from .invitation_views import (
    InviteCandidatesView,
    InvitationListView,
    RevokeInvitationView,
    CandidateInvitationDetailView,
)

urlpatterns = [
    # Assessment CRUD
    path(
        "assessments/",
        RecruiterAssessmentListCreateView.as_view(),
        name="recruiter-assessment-list",
    ),
    path(
        "assessments/<int:pk>/",
        RecruiterAssessmentDetailView.as_view(),
        name="recruiter-assessment-detail",
    ),
    path(
        "assessments/<int:pk>/publish/",
        RecruiterAssessmentPublishView.as_view(),
        name="recruiter-assessment-publish",
    ),
    # Problem management
    path(
        "assessments/<int:assessment_id>/problems/",
        RecruiterProblemCreateView.as_view(),
        name="recruiter-problem-create",
    ),
    path(
        "assessments/<int:assessment_id>/problems/<int:pk>/",
        RecruiterProblemDetailView.as_view(),
        name="recruiter-problem-detail",
    ),
    path(
        "assessments/<int:assessment_id>/problems/<int:problem_id>/test-cases/",
        RecruiterTestCasesUploadView.as_view(),
        name="recruiter-test-cases-upload",
    ),
    # Candidate invitation management
    path(
        "assessments/<int:assessment_id>/invite/",
        InviteCandidatesView.as_view(),
        name="recruiter-invite-candidates",
    ),
    path(
        "assessments/<int:assessment_id>/invitations/",
        InvitationListView.as_view(),
        name="recruiter-invitation-list",
    ),
    path(
        "invitations/<str:invitation_id>/revoke/",
        RevokeInvitationView.as_view(),
        name="recruiter-invitation-revoke",
    ),
    # Public candidate invitation detail (token-based, no auth)
    path(
        "invitation/<str:token>/",
        CandidateInvitationDetailView.as_view(),
        name="candidate-invitation-detail",
    ),
]

# Refactor: Improve error handling and exception logging.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Optimize imports and clean up code structure.

# Refactor: Update validation checks and constraints.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Fix minor edge cases in calculation functions.
