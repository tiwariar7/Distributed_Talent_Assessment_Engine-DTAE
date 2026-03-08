"""
Recruiter-only permissions scoped to the user's organization.
"""

from apps.accounts.models import Membership
from apps.accounts.permissions import HasMembershipRole
from apps.assessments.models import Assessment
from apps.organizations.models import Organization


def recruiter_organization_resolver(view, request) -> Organization | None:
    """Adapter for ``HasMembershipRole`` (view, request) signature."""
    return get_recruiter_organization(request)


def get_recruiter_organization(request) -> Organization | None:
    """
    Resolve the recruiter's organization from query param or first membership.

    Query param ``organization`` (slug) takes precedence when the user belongs
    to multiple organizations.
    """
    slug = request.query_params.get("organization") or request.data.get("organization_slug")
    memberships = Membership.objects.filter(
        user=request.user,
        role__code="recruiter",
    ).select_related("organization")

    if slug:
        membership = memberships.filter(organization__slug=slug).first()
        return membership.organization if membership else None

    membership = memberships.first()
    return membership.organization if membership else None


def assessment_organization_resolver(view, request) -> Organization | None:
    """Resolve organization from an assessment primary key in the URL."""
    assessment_id = view.kwargs.get("pk") or view.kwargs.get("assessment_id")
    if not assessment_id:
        return get_recruiter_organization(request)

    try:
        return Assessment.objects.select_related("organization").get(
            pk=assessment_id,
        ).organization
    except Assessment.DoesNotExist:
        return None


class IsRecruiter(HasMembershipRole):
    """Require recruiter role in the resolved organization."""

    def has_permission(self, request, view) -> bool:
        view.required_role = "recruiter"
        view.organization_resolver = recruiter_organization_resolver
        return super().has_permission(request, view)


class IsRecruiterForAssessment(HasMembershipRole):
    """Require recruiter role for the assessment's owning organization."""

    def has_permission(self, request, view) -> bool:
        view.required_role = "recruiter"
        view.organization_resolver = assessment_organization_resolver
        return super().has_permission(request, view)

# Refactor: Optimize query performance and database indexing.

# Refactor: Improve responsive styles and layouts.
