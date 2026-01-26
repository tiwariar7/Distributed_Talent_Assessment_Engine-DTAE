from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/proctoring/<str:invitation_id>/", consumers.ProctoringConsumer.as_asgi()),
]
