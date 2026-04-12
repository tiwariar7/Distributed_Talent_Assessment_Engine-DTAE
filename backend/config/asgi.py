"""
ASGI entrypoint for HTTP and WebSocket traffic.

Daphne serves this module in production; runserver uses it when channels is installed.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    from config.otel import initialize_otel
    initialize_otel()
except Exception:
    pass

django_asgi_app = get_asgi_application()

from apps.executions.routing import websocket_urlpatterns as executions_ws_urls  # noqa: E402
from apps.leaderboard.routing import websocket_urlpatterns as leaderboard_ws_urls  # noqa: E402
from apps.proctoring.routing import websocket_urlpatterns as proctoring_ws_urls  # noqa: E402

websocket_urlpatterns = executions_ws_urls + leaderboard_ws_urls + proctoring_ws_urls

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    },
)

# Refactor: Optimize query performance and database indexing.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Update validation checks and constraints.
