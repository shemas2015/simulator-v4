import json
import time
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
#from .connection_manager import connection_manager
import logging
from motion_control.arduino_controller import ArduinoController

logger = logging.getLogger(__name__)

# Global list to manage ArduinoController instances
arduino_controllers = {}

# Global instance for active listening session
active_listener = None








