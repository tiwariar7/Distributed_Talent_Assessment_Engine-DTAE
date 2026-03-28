from django.urls import path
from .consumers import LeaderboardConsumer

websocket_urlpatterns = [
    path("ws/leaderboard/<int:assessment_id>/", LeaderboardConsumer.as_asgi()),
]

# Refactor: Improve responsive styles and layouts.

# Refactor: Optimize query performance and database indexing.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Update validation checks and constraints.
