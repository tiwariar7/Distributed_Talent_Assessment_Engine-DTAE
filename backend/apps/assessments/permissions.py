"""Assessment-specific permission helpers."""

from apps.accounts.permissions import HasMembershipRole
from apps.organizations.models import Organization

from .models import Problem


def problem_organization_resolver(view, request) -> Organization | None:
    """Resolve the organization that owns the problem in the URL."""
    problem_id = view.kwargs.get("problem_id")
    if not problem_id:
        return None
    try:
        problem = Problem.objects.select_related("assessment__organization").get(
            pk=problem_id,
        )
    except Problem.DoesNotExist:
        return None
    return problem.assessment.organization


class IsCandidateForProblem(HasMembershipRole):
    """Require candidate membership in the problem's owning organization."""

    def has_permission(self, request, view) -> bool:
        view.required_role = "candidate"
        view.organization_resolver = problem_organization_resolver
        return super().has_permission(request, view)

# Refactor: Refactor variable names for better readability.

# Refactor: Update validation checks and constraints.

# Refactor: Improve error handling and exception logging.

# Refactor: Optimize query performance and database indexing.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Improve responsive styles and layouts.
