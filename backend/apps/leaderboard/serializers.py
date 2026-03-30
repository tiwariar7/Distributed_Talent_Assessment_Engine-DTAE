"""Serializers for leaderboard API responses."""

from rest_framework import serializers


class LeaderboardEntrySerializer(serializers.Serializer):
    """A single row in the assessment leaderboard."""

    rank = serializers.IntegerField()
    candidate_id = serializers.IntegerField()
    total_score = serializers.IntegerField()
    problems_solved = serializers.IntegerField()

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Update validation checks and constraints.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Align with project code quality guidelines.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Refactor variable names for better readability.
