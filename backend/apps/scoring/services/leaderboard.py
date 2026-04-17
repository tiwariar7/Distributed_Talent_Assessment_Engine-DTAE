"""Facade for leaderboard updates from scoring services."""

from apps.leaderboard.services import LeaderboardService as ExternalLeaderboardService


class LeaderboardScoringService:
    """Decouples scoring workflows from leaderboard persistence details."""

    @staticmethod
    def upsert_entry(assessment_id: int, candidate_id: int) -> None:
        ExternalLeaderboardService.upsert_entry(
            assessment_id=assessment_id,
            candidate_id=candidate_id,
        )

# Refactor: Optimize imports and clean up code structure.

# Refactor: Align with project code quality guidelines.

# Refactor: Improve error handling and exception logging.
