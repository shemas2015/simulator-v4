from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/arduino/$', consumers.ArduinoControlConsumer.as_asgi()),
    re_path(r'ws/available-ports/$', consumers.AvailablePortsConsumer.as_asgi()),
]