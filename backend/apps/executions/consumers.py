"""
WebSocket consumer for live submission execution updates.

Clients connect with a JWT query parameter and receive events published by
Celery workers via Redis channel layer.
"""

from __future__ import annotations

import logging
import time
from urllib.parse import parse_qs

import redis.asyncio as aioredis
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.assessments.models import Submission
from infrastructure.couchdb import DocumentRepository

logger = logging.getLogger(__name__)
User = get_user_model()


class SubmissionExecutionConsumer(AsyncJsonWebsocketConsumer):
    """
    Stream submission status and CouchDB log entries to the owning candidate.

    URL: ws://host/ws/submissions/<submission_id>/?token=<jwt_access_token>
    """

    async def connect(self) -> None:
        """Authenticate, authorize, and join the submission channel group."""
        self.submission_id = int(self.scope["url_route"]["kwargs"]["submission_id"])
        
        user = await self._authenticate_user()
        if user is None:
            await self.close(code=4001)
            return

        if not await self._user_owns_submission(user):
            await self.close(code=4003)
            return

        # Enforce per-user concurrent socket connection limits in Redis
        self.redis_client = aioredis.from_url(settings.REDIS_URL)
        user_conn_key = f"ws_conn_count:{user.pk}"
        try:
            conn_count = await self.redis_client.incr(user_conn_key)
            await self.redis_client.expire(user_conn_key, 3600)  # 1 hour safety expiry
            if conn_count > 10:  # Max 10 connections per user
                await self.redis_client.decr(user_conn_key)
                await self.redis_client.close()
                await self.close(code=4005)  # Limit exceeded code
                return
        except Exception as e:
            logger.error("Redis connection limit check failed: %s", e)

        self.group_name = f"submission_{self.submission_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        try:
            from config.prometheus_middleware import WEBSOCKET_CONNECTIONS
            WEBSOCKET_CONNECTIONS.inc()
        except Exception:
            pass

        submission = await self._get_submission()
        await self.send_json(
            {
                "type": "connected",
                "submission_id": self.submission_id,
                "status": submission.status,
                "score": submission.score,
            },
        )

        # Support Event Replay: stream existing CouchDB log entries on connect/reconnect
        existing_logs = await self._get_existing_logs(submission.couchdb_execution_log_doc_id)
        if existing_logs:
            await self.send_json(
                {
                    "type": "event_replay",
                    "submission_id": self.submission_id,
                    "entries": existing_logs,
                }
            )

    async def disconnect(self, close_code: int) -> None:
        """Leave the submission group on disconnect and clean up Redis limits."""
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

        try:
            from config.prometheus_middleware import WEBSOCKET_CONNECTIONS
            WEBSOCKET_CONNECTIONS.dec()
        except Exception:
            pass

        if hasattr(self, "redis_client") and self.scope.get("user") and self.scope["user"].is_authenticated:
            user_conn_key = f"ws_conn_count:{self.scope['user'].pk}"
            try:
                await self.redis_client.decr(user_conn_key)
                await self.redis_client.close()
            except Exception as e:
                logger.error("Failed to decrement connection limits: %s", e)

    async def submission_event(self, event: dict) -> None:
        """Forward group events to the WebSocket client after checking token expiry."""
        if hasattr(self, "token_expiry") and time.time() > self.token_expiry:
            await self.send_json({"type": "error", "message": "Access token expired."})
            await self.close(code=4002)
            return

        await self.send_json(event["event"])

    async def _authenticate_user(self) -> User | None:
        """Validate JWT from query string ``token`` parameter and track expiry."""
        query_string = self.scope.get("query_string", b"").decode()
        token_list = parse_qs(query_string).get("token", [])
        if not token_list:
            return None

        try:
            access = AccessToken(token_list[0])
            user_id = access["user_id"]
            self.token_expiry = access["exp"]
            user = await database_sync_to_async(User.objects.get)(pk=user_id)
            self.scope["user"] = user
            return user
        except (InvalidToken, TokenError, User.DoesNotExist, KeyError) as exc:
            logger.warning("WebSocket auth failed: %s", exc)
            return None

    @database_sync_to_async
    def _user_owns_submission(self, user: User) -> bool:
        """Only the submitting candidate may subscribe to execution events."""
        return Submission.objects.filter(
            pk=self.submission_id,
            candidate=user,
        ).exists()

    @database_sync_to_async
    def _get_submission(self) -> Submission:
        return Submission.objects.get(pk=self.submission_id)

    @database_sync_to_async
    def _get_existing_logs(self, log_doc_id: str) -> list[dict]:
        """Fetch historical log entries from CouchDB."""
        try:
            repo = DocumentRepository()
            return repo.get_execution_log_entries(log_doc_id)
        except Exception as e:
            logger.warning("Failed to fetch historical logs from CouchDB: %s", e)
            return []

# Refactor: Optimize imports and clean up code structure.
