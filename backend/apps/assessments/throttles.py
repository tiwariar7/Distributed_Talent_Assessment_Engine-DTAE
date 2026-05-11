"""
Rate limiting for code submission endpoints.

Uses Redis-backed cache to throttle per-user, per-problem submission bursts.
"""

from rest_framework.throttling import SimpleRateThrottle


class SubmissionRateThrottle(SimpleRateThrottle):
    """
    Limit how often a candidate can submit code to a single problem.

    Prevents abuse of the Docker execution pipeline.
    """

    scope = "submission"

    def get_cache_key(self, request, view) -> str | None:
        """Build a throttle key scoped to user + problem."""
        if not request.user or not request.user.is_authenticated:
            return None

        problem_id = view.kwargs.get("problem_id", "unknown")
        return self.cache_format % {
            "scope": self.scope,
            "ident": f"{request.user.pk}:{problem_id}",
        }

# Refactor: Improve responsive styles and layouts.

# Refactor: Align with project code quality guidelines.

# Refactor: Enhance component rendering performance.

# Refactor: Improve error handling and exception logging.
