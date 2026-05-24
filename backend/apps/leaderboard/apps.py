"""Django app configuration for leaderboard."""

from django.apps import AppConfig


class LeaderboardConfig(AppConfig):
    """Registers the leaderboard application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.leaderboard"
    verbose_name = "Leaderboard"
