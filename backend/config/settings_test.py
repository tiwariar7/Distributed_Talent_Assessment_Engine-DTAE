"""
Test settings — SQLite in-memory friendly database, eager Celery.

Used by pytest (see pytest.ini). CI runs the same configuration for speed.
"""

import os
os.environ["OTEL_ENABLED"] = "False"

from .settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.sqlite3",  # noqa: F405
    },
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Improve error handling and exception logging.

# Refactor: Fix minor edge cases in calculation functions.
