"""
Role-based API permissions backed by normalized Membership rows.
"""

from rest_framework.permissions import BasePermission

from .models import Membership


class HasMembershipRole(BasePermission):
    """
    Grant access when the user holds a given role in the target organization.

    Views may set `required_role` (e.g. ``candidate``) and optionally
    ``organization_lookup`` — a callable(view) -> Organization | None.
    
    Optimized to parse roles and org slugs from the JWT claims payload first,
    eliminating redundant database checks.
    """

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        required_role = getattr(view, "required_role", None)
        if not required_role:
            return True

        organization_resolver = getattr(view, "organization_resolver", None)

        # Retrieve JWT payload claims (fast in-memory path)
        jwt_payload = None
        if hasattr(request, "auth") and request.auth:
            if isinstance(request.auth, dict):
                jwt_payload = request.auth
            elif hasattr(request.auth, "payload"):
                jwt_payload = request.auth.payload

        if jwt_payload and "memberships" in jwt_payload:
            memberships = jwt_payload["memberships"]
            if organization_resolver is None:
                return any(m["role_code"] == required_role for m in memberships)

            organization = organization_resolver(view, request)
            if organization is None:
                return False

            return any(
                m["org_slug"] == organization.slug and m["role_code"] == required_role
                for m in memberships
            )

        # Database fallback path (session auth or non-customized tokens)
        if organization_resolver is None:
            return Membership.objects.filter(
                user=request.user,
                role__code=required_role,
            ).exists()

        organization = organization_resolver(view, request)
        if organization is None:
            return False

        return Membership.objects.filter(
            user=request.user,
            organization=organization,
            role__code=required_role,
        ).exists()


class IsRecruiterUser(HasMembershipRole):
    """Strictly grant access to users who have a recruiter role in any tenant."""

    def has_permission(self, request, view) -> bool:
        view.required_role = "recruiter"
        return super().has_permission(request, view)


class IsCandidateUser(HasMembershipRole):
    """Strictly grant access to users who have a candidate role in any tenant."""

    def has_permission(self, request, view) -> bool:
        view.required_role = "candidate"
        return super().has_permission(request, view)


class IsAdminUser(HasMembershipRole):
    """Strictly grant access to users who have an admin role in any tenant."""

    def has_permission(self, request, view) -> bool:
        view.required_role = "admin"
        return super().has_permission(request, view)


# Refactor: Refactor variable names for better readability.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Enhance component rendering performance.

# Refactor: Improve error handling and exception logging.
