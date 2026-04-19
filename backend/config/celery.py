"""Celery application for asynchronous code execution tasks."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    from config.otel import initialize_otel
    initialize_otel()
except Exception:
    pass

app = Celery("dtae")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Refactor: Enhance component rendering performance.

# Refactor: Optimize imports and clean up code structure.

# Refactor: Improve responsive styles and layouts.
