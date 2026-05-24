"""
Dependency health probes for Kubernetes-style readiness checks.
"""

from __future__ import annotations

import logging
from typing import Callable

import redis
import requests
from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)


def check_postgresql() -> tuple[bool, str]:
    """Verify PostgreSQL accepts connections."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True, "ok"
    except Exception as exc:
        logger.warning("PostgreSQL health check failed: %s", exc)
        return False, str(exc)


def check_couchdb() -> tuple[bool, str]:
    """Verify CouchDB is reachable."""
    try:
        response = requests.get(
            f"{settings.COUCHDB_URL.rstrip('/')}/_up",
            auth=(settings.COUCHDB_USER, settings.COUCHDB_PASSWORD),
            timeout=3,
        )
        if response.status_code == 200:
            return True, "ok"
        return False, f"status_{response.status_code}"
    except Exception as exc:
        logger.warning("CouchDB health check failed: %s", exc)
        return False, str(exc)


def check_redis() -> tuple[bool, str]:
    """Verify Redis accepts connections."""
    try:
        client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        client.ping()
        return True, "ok"
    except Exception as exc:
        logger.warning("Redis health check failed: %s", exc)
        return False, str(exc)


READINESS_CHECKS: dict[str, Callable[[], tuple[bool, str]]] = {
    "postgresql": check_postgresql,
    "couchdb": check_couchdb,
    "redis": check_redis,
}
