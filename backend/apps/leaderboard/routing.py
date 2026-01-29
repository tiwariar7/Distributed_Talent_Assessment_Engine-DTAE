from django.urls import path
from .consumers import LeaderboardConsumer

websocket_urlpatterns = [
    path("ws/leaderboard/<int:assessment_id>/", LeaderboardConsumer.as_asgi()),
]
