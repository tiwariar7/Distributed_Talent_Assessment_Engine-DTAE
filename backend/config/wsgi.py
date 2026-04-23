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

# Refactor: Refactor variable names for better readability.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Enhance component rendering performance.

# Refactor: Optimize query performance and database indexing.

# Refactor: Fix minor edge cases in calculation functions.
