from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # This matches the '/ws' URL your Python script is trying to connect to!
    re_path(r'^ws$', consumers.DeviceConsumer.as_asgi()),
]
