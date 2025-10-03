import json
import time
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .connection_manager import connection_manager
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
def get_connections(request):
    """
    Get all current motor connections.

    Returns:
        JSON response with all connections
    """
    connections = connection_manager.get_all_connections()
    return Response({
        'connections': connections,
        'count': len(connections)
    })


@api_view(['GET'])
def get_connection_status(request, port):
    """
    Get connection status for a specific port.

    Args:
        port: Serial port identifier

    Returns:
        JSON response with connection info
    """
    connection = connection_manager.get_connection(port)

    if connection:
        return Response(connection)
    else:
        return Response(
            {'error': 'Connection not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def update_motor_position(request, port):
    """
    Update motor position (left/right).

    Args:
        port: Serial port identifier

    Expected body:
        {
            "position": "left" | "right"
        }
    """
    position = request.data.get('position')

    if position not in ['left', 'right']:
        return Response(
            {'error': 'Invalid position. Must be "left" or "right"'},
            status=status.HTTP_400_BAD_REQUEST
        )

    connection = connection_manager.get_connection(port)
    if not connection:
        return Response(
            {'error': 'Connection not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    connection_manager.update_motor_position(port, position)

    return Response({
        'port': port,
        'position': position,
        'success': True
    })


def connection_events_stream(request):
    """
    Server-Sent Events (SSE) endpoint for real-time connection updates.

    Streams connection status changes to the frontend.
    """
    def event_stream():
        # Send initial connection state
        connections = connection_manager.get_all_connections()
        yield f"data: {json.dumps({'type': 'init', 'connections': connections})}\n\n"

        # Track last sent state to only send changes
        last_state = connections.copy()

        # Listener callback for connection changes
        changes = []

        def on_change(new_connections):
            changes.append(new_connections)

        # Register listener
        connection_manager.add_listener(on_change)

        try:
            # Keep connection alive and send updates
            while True:
                if changes:
                    # Get latest change
                    new_connections = changes.pop()

                    # Only send if state actually changed
                    if new_connections != last_state:
                        yield f"data: {json.dumps({'type': 'update', 'connections': new_connections})}\n\n"
                        last_state = new_connections.copy()

                # Send heartbeat every 15 seconds to keep connection alive
                yield f": heartbeat\n\n"
                time.sleep(1)

        except GeneratorExit:
            # Client disconnected
            connection_manager.remove_listener(on_change)
            logger.info("SSE client disconnected")

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'

    return response
