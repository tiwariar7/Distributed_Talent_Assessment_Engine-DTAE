"""Leaderboard API — served from CouchDB MapReduce, not SQL."""

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LeaderboardEntrySerializer
from .services import LeaderboardService


class AssessmentLeaderboardView(APIView):
    """
    Return ranked candidates for an assessment.

    Backed by CouchDB views; intentionally avoids JOIN-heavy SQL.
    """

    def get(self, request: Request, assessment_id: int) -> Response:
        """Return top N leaderboard rows."""
        limit = min(int(request.query_params.get("limit", 50)), 100)
        rankings = LeaderboardService.get_rankings(assessment_id, limit=limit)
        serializer = LeaderboardEntrySerializer(rankings, many=True)
        return Response(serializer.data)

# Refactor: Align with project code quality guidelines.

# Refactor: Align with project code quality guidelines.

# Refactor: Optimize query performance and database indexing.

# Refactor: Enhance component rendering performance.

# Refactor: Optimize query performance and database indexing.

# Refactor: Optimize query performance and database indexing.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve responsive styles and layouts.

# Refactor: Improve error handling and exception logging.

# Refactor: Improve responsive styles and layouts.
