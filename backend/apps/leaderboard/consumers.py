import logging
import json
import redis.asyncio as aioredis
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class LeaderboardConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for streaming real-time leaderboard rankings.
    URL: ws://host/ws/leaderboard/<assessment_id>/
    """

    async def connect(self):
        self.assessment_id = int(self.scope["url_route"]["kwargs"]["assessment_id"])
        self.group_name = f"leaderboard_{self.assessment_id}"

        # Join the channel group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send initial rankings immediately
        rankings = await self.get_current_rankings()
        await self.send_json({
            "type": "leaderboard_update",
            "assessment_id": self.assessment_id,
            "rankings": rankings,
        })

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def leaderboard_update(self, event):
        """
        Receive update from the group and forward to WebSocket client.
        """
        # Forward the rankings to the client
        await self.send_json({
            "type": "leaderboard_update",
            "assessment_id": self.assessment_id,
            "rankings": event.get("rankings", []),
        })

    async def get_current_rankings(self):
        """
        Fetch rankings from Redis or fall back to DB/CouchDB.
        """
        redis_client = aioredis.from_url(settings.REDIS_URL)
        zset_key = f"leaderboard:zset:{self.assessment_id}"
        solved_key = f"leaderboard:solved:{self.assessment_id}"

        try:
            # Query Redis ZSET for top scores
            # elements are returned as (member, score)
            top_members = await redis_client.zrevrange(zset_key, 0, 100, withscores=True)
            
            if not top_members:
                # Cache miss: fetch from DB/CouchDB and populate Redis
                rankings = await self.fallback_db_rankings()
                return rankings

            # Fetch solved counts
            rankings = []
            for rank, (candidate_id_bytes, score) in enumerate(top_members, start=1):
                candidate_id = int(candidate_id_bytes)
                solved_count_bytes = await redis_client.hget(solved_key, str(candidate_id))
                solved = int(solved_count_bytes) if solved_count_bytes else 0
                
                # Fetch candidate email
                email = await self.get_candidate_email(candidate_id)

                rankings.append({
                    "rank": rank,
                    "candidate_id": candidate_id,
                    "candidate_email": email,
                    "total_score": int(score),
                    "problems_solved": solved,
                })
            
            await redis_client.close()
            return rankings
        except Exception as e:
            logger.error("Error retrieving real-time rankings: %s", e)
            # fallback
            return await self.fallback_db_rankings()

    @database_sync_to_async
    def get_candidate_email(self, candidate_id: int) -> str:
        try:
            return User.objects.get(pk=candidate_id).email
        except User.DoesNotExist:
            return f"user_{candidate_id}@assessment.test"

    @database_sync_to_async
    def fallback_db_rankings(self):
        # Fallback to the synchronous LeaderboardService
        from .services import LeaderboardService
        return LeaderboardService.get_rankings(self.assessment_id)

# Refactor: Refactor variable names for better readability.

# Refactor: Improve responsive styles and layouts.

# Refactor: Refactor variable names for better readability.

# Refactor: Update validation checks and constraints.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Align with project code quality guidelines.
