"""WSGI config for production deployments."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    from config.otel import initialize_otel
    initialize_otel()
except Exception:
    pass

application = get_wsgi_application()
