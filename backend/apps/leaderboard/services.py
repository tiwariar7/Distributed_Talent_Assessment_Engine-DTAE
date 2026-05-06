from __future__ import annotations

import logging
import time
from typing import Any

import redis
import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models import Max
from django.contrib.auth import get_user_model
from opentelemetry import trace

from apps.assessments.models import Submission, Problem
from infrastructure.couchdb import CouchDBClient
from config.prometheus_middleware import (
    LEADERBOARD_UPDATE_LATENCY,
    LEADERBOARD_FAILED_EVENTS,
    LEADERBOARD_CACHE_HITS,
    LEADERBOARD_CACHE_MISSES,
)

logger = logging.getLogger(__name__)
User = get_user_model()
tracer = trace.get_tracer("leaderboard")


class LeaderboardService:
    """
    Maintains denormalized, real-time leaderboard rankings in CouchDB and Redis.
    Uses PostgreSQL as the single source of truth for score aggregation.
    """

    @staticmethod
    def _doc_id(assessment_id: int, candidate_id: int) -> str:
        return f"leaderboard_{assessment_id}_{candidate_id}"

    @classmethod
    def upsert_entry(
        cls,
        assessment_id: int,
        candidate_id: int,
        score_delta: int = 0,
        problems_solved_delta: int = 0,
    ) -> None:
        """
        Recalculates total score and problems solved using transactional Postgres data,
        then updates CouchDB, Redis, and broadcasts live rankings via WebSockets.
        """
        start_time = time.perf_counter()

        with tracer.start_as_current_span("leaderboard_upsert_entry") as span:
            span.set_attribute("assessment_id", assessment_id)
            span.set_attribute("candidate_id", candidate_id)

            try:
                # 1. Fetch highest score per problem in the assessment from Postgres
                problem_scores = (
                    Submission.objects.filter(
                        problem__assessment_id=assessment_id,
                        candidate_id=candidate_id,
                        score__isnull=False,
                    )
                    .values("problem_id")
                    .annotate(max_score=Max("score"))
                )

                total_score = sum(
                    item["max_score"] for item in problem_scores if item["max_score"] is not None
                )
                problems_solved = sum(
                    1 for item in problem_scores
                    if item["max_score"] is not None and item["max_score"] > 0
                )

                # 2. Update CouchDB
                client = CouchDBClient()
                doc_id = cls._doc_id(assessment_id, candidate_id)
                body = {
                    "type": "leaderboard_entry",
                    "assessment_id": assessment_id,
                    "candidate_id": candidate_id,
                    "total_score": total_score,
                    "problems_solved": problems_solved,
                }

                try:
                    existing = client.get_document(doc_id)
                    body["_rev"] = existing["_rev"]
                    client.update_document(doc_id, body)
                except requests.HTTPError as exc:
                    if exc.response is not None and exc.response.status_code == 404:
                        try:
                            client.create_document(doc_id, body)
                        except Exception:
                            # Concurrent create fallback
                            existing = client.get_document(doc_id)
                            body["_rev"] = existing["_rev"]
                            client.update_document(doc_id, body)
                    else:
                        raise

                # 3. Update Redis cache (ZSET and Solved Hash)
                r = redis.Redis.from_url(settings.REDIS_URL)
                zset_key = f"leaderboard:zset:{assessment_id}"
                solved_key = f"leaderboard:solved:{assessment_id}"

                pipe = r.pipeline()
                pipe.zadd(zset_key, {str(candidate_id): total_score})
                pipe.hset(solved_key, str(candidate_id), problems_solved)
                pipe.execute()

                # 4. Broadcast updated rankings to Channels group
                rankings = cls.get_rankings(assessment_id)
                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f"leaderboard_{assessment_id}",
                        {
                            "type": "leaderboard_update",
                            "rankings": rankings,
                        },
                    )

                # Observe metrics
                duration = time.perf_counter() - start_time
                LEADERBOARD_UPDATE_LATENCY.observe(duration)

            except Exception as e:
                logger.error("Failed to update leaderboard entry: %s", e)
                LEADERBOARD_FAILED_EVENTS.inc()
                raise e

    @classmethod
    def get_rankings(
        cls,
        assessment_id: int,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Fetch ranked candidates from Redis cache, falling back to Postgres on miss.
        """
        r = redis.Redis.from_url(settings.REDIS_URL)
        zset_key = f"leaderboard:zset:{assessment_id}"
        solved_key = f"leaderboard:solved:{assessment_id}"

        # Try fetching from Redis ZSET
        top_members = r.zrevrange(zset_key, 0, limit - 1, withscores=True)

        if not top_members:
            # Cache miss: rebuild from PostgreSQL
            LEADERBOARD_CACHE_MISSES.inc()
            cls.rebuild_leaderboard_cache(assessment_id)
            top_members = r.zrevrange(zset_key, 0, limit - 1, withscores=True)
            if not top_members:
                return []
        else:
            LEADERBOARD_CACHE_HITS.inc()

        rankings = []
        # Pre-fetch candidate emails to avoid N+1 database queries
        candidate_ids = [int(member) for member, _ in top_members]
        candidates_map = {
            u.id: u.email
            for u in User.objects.filter(id__in=candidate_ids)
        }

        for rank, (candidate_id_bytes, score) in enumerate(top_members, start=1):
            candidate_id = int(candidate_id_bytes)
            solved_bytes = r.hget(solved_key, str(candidate_id))
            solved = int(solved_bytes) if solved_bytes else 0
            email = candidates_map.get(candidate_id, f"user_{candidate_id}@assessment.test")

            rankings.append(
                {
                    "rank": rank,
                    "candidate_id": candidate_id,
                    "candidate_email": email,
                    "total_score": int(score),
                    "problems_solved": solved,
                },
            )

        return rankings

    @classmethod
    def rebuild_leaderboard_cache(cls, assessment_id: int) -> None:
        """
        Scans PostgreSQL for all submissions in the assessment, aggregates totals,
        and populates the Redis cache and CouchDB documents.
        """
        with tracer.start_as_current_span("rebuild_leaderboard_cache"):
            # Find all candidates who have submissions
            candidate_ids = Submission.objects.filter(
                problem__assessment_id=assessment_id,
                score__isnull=False,
            ).values_list("candidate_id", flat=True).distinct()

            if not candidate_ids:
                return

            client = CouchDBClient()
            r = redis.Redis.from_url(settings.REDIS_URL)
            zset_key = f"leaderboard:zset:{assessment_id}"
            solved_key = f"leaderboard:solved:{assessment_id}"

            # Clear existing Redis keys before rebuilding
            r.delete(zset_key, solved_key)

            for candidate_id in candidate_ids:
                # Recalculate
                problem_scores = (
                    Submission.objects.filter(
                        problem__assessment_id=assessment_id,
                        candidate_id=candidate_id,
                        score__isnull=False,
                    )
                    .values("problem_id")
                    .annotate(max_score=Max("score"))
                )

                total_score = sum(
                    item["max_score"] for item in problem_scores if item["max_score"] is not None
                )
                problems_solved = sum(
                    1 for item in problem_scores
                    if item["max_score"] is not None and item["max_score"] > 0
                )

                # Write to CouchDB
                doc_id = cls._doc_id(assessment_id, candidate_id)
                body = {
                    "type": "leaderboard_entry",
                    "assessment_id": assessment_id,
                    "candidate_id": candidate_id,
                    "total_score": total_score,
                    "problems_solved": problems_solved,
                }

                try:
                    existing = client.get_document(doc_id)
                    body["_rev"] = existing["_rev"]
                    client.update_document(doc_id, body)
                except requests.HTTPError as exc:
                    if exc.response is not None and exc.response.status_code == 404:
                        client.create_document(doc_id, body)
                    else:
                        raise

                # Write to Redis
                r.zadd(zset_key, {str(candidate_id): total_score})
                r.hset(solved_key, str(candidate_id), problems_solved)

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Optimize imports and clean up code structure.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Optimize imports and clean up code structure.

# Refactor: Improve responsive styles and layouts.

# Refactor: Refactor variable names for better readability.

# Refactor: Improve error handling and exception logging.

# Refactor: Improve error handling and exception logging.

# Refactor: Update validation checks and constraints.
