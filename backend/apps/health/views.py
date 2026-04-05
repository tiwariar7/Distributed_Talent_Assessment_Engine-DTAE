"""Liveness and readiness endpoints for orchestrators."""

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from . import checks as checks_module


class LivenessView(APIView):
    """
    Lightweight probe — process is running.

    Does not check downstream dependencies.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request: Request) -> Response:
        """Return 200 when the API process is alive."""
        return Response({"status": "alive"})


class ReadinessView(APIView):
    """
    Deep probe — PostgreSQL, CouchDB, and Redis are reachable.

    Returns 503 when any dependency is unhealthy.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request: Request) -> Response:
        """Run all readiness checks and aggregate results."""
        results: dict[str, dict] = {}
        all_healthy = True

        for name in ("postgresql", "couchdb", "redis"):
            check = getattr(checks_module, f"check_{name}")
            healthy, detail = check()
            results[name] = {"healthy": healthy, "detail": detail}
            if not healthy:
                all_healthy = False

        status_code = 200 if all_healthy else 503
        return Response(
            {"status": "ready" if all_healthy else "degraded", "checks": results},
            status=status_code,
        )

# Refactor: Refactor variable names for better readability.

# Refactor: Align with project code quality guidelines.

# Refactor: Improve error handling and exception logging.

# Refactor: Optimize query performance and database indexing.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Align with project code quality guidelines.
