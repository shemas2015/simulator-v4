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


@api_view(['GET'])
def add_motor(request, motor_number, device):
    """
    Add a motor to ArduinoController list.

    Args:
        motor_number: Motor number (0 for left, 1 for right)
        device: Device port (e.g., "COM5", "/dev/ttyUSB0")

    Returns:
        JSON response with motor info
    """
    try:
        motor_number = int(motor_number)

        # Validate motor number
        if motor_number not in [0, 1]:
            return Response(
                {'error': 'Motor number must be 0 (left) or 1 (right)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if motor already exists
        if motor_number in arduino_controllers:
            return Response(
                {'error': f'Motor {motor_number} already exists'},
                status=status.HTTP_409_CONFLICT
            )

        # Check if device exists in available ports
        available_ports = ArduinoController.get_available_ports()
        available_devices = [port['device'] for port in available_ports]

        if device not in available_devices:
            return Response(
                {'error': f'Device {device} not found in available ports. Available: {available_devices}'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create Arduino controller
        arduino = ArduinoController(
            port=device,
            baudrate=9600,
            motor_number=motor_number
        )

        # Check if connection was successful
        if not arduino._is_connected:
            return Response(
                {'error': f'Failed to connect to device {device}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Add to controllers list
        arduino_controllers[motor_number] = {
            'controller': arduino,
            'device': device,
            'motor_number': motor_number,
            'position': 'left' if motor_number == 0 else 'right',
            'connected': True
        }

        logger.info(f"Motor {motor_number} added on device {device}")

        return Response({
            'success': True,
            'motor_number': motor_number,
            'device': device,
            'position': 'left' if motor_number == 0 else 'right',
            'connected': True
        })

    except ValueError:
        return Response(
            {'error': 'Invalid motor number format'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error adding motor: {e}")
        return Response(
            {'error': f'Failed to add motor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def get_motors(request):
    """
    Server-Sent Events (SSE) endpoint for motors.
    Returns all connected motors in real-time.
    """
    def event_stream():
        try:
            while True:
                # Get all connected motors
                motors = []
                for motor_number, motor_info in arduino_controllers.items():
                    motors.append({
                        'motor_number': motor_number,
                        'device': motor_info['device'],
                        'position': motor_info['position'],
                        'connected': motor_info['connected']
                    })

                # Send current motors
                yield f"data: {json.dumps({'motors': motors, 'count': len(motors)})}\n\n"

                # Check every 3 seconds
                time.sleep(3)

        except GeneratorExit:
            logger.info("SSE client disconnected")

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'

    return response


@api_view(['GET'])
def get_available_ports(request):
    """
    Get all available Arduino/ESP32 ports.

    Returns:
        JSON response with all available ports
    """
    try:
        available_ports = ArduinoController.get_available_ports()

        return Response({
            'available_ports': available_ports,
            'count': len(available_ports)
        })

    except Exception as e:
        logger.error(f"Error getting available ports: {e}")
        return Response(
            {'error': f'Failed to get available ports: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def remove_motor(request, motor_number):
    """
    Remove a motor from ArduinoController list.

    Args:
        motor_number: Motor number to remove

    Returns:
        JSON response with result
    """
    try:
        motor_number = int(motor_number)

        if motor_number not in arduino_controllers:
            return Response(
                {'error': f'Motor {motor_number} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Disconnect and remove
        motor_info = arduino_controllers[motor_number]
        if motor_info['controller'].connection:
            motor_info['controller'].connection.close()

        del arduino_controllers[motor_number]

        logger.info(f"Motor {motor_number} removed")

        return Response({
            'success': True,
            'message': f'Motor {motor_number} removed'
        })

    except ValueError:
        return Response(
            {'error': 'Invalid motor number format'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error removing motor: {e}")
        return Response(
            {'error': f'Failed to remove motor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


