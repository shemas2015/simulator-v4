import json
import logging
import asyncio
import threading
import os
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from motion_control.arduino_controller import ArduinoController
from motion_control.assetto_physics import AssettoPhysics

logger = logging.getLogger(__name__)


class ArduinoControlConsumer(WebsocketConsumer):
    """
    WebSocket consumer for real-time Arduino motor control.
    Manages separate controllers for left (0) and right (1) motors.
    """

    def connect(self):
        """Accept WebSocket connection."""
        self.motors = {}  # Store motor instances: {0: left, 1: right}
        self.ac_physics = None  # Assetto Corsa physics instance
        self.monitoring_thread = None  # Background monitoring thread
        self.accept()
        logger.info("WebSocket connected, awaiting motor configuration")

    def disconnect(self, close_code):
        """Clean up all Arduino connections on WebSocket disconnect."""
        if hasattr(self, 'motors'):
            for motor_num, arduino in self.motors.items():
                if arduino and arduino.is_connected():
                    arduino.disconnect()
                    logger.info(f"Disconnected motor {motor_num}")

    def receive(self, text_data):
        """
        Handle incoming commands.

        Connect motor: {"action": "connect", "port": "COM3", "motor": 0}
        Send command: {"action": "command", "motor": 0, "command": "f"}
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'connect':
                port = data.get('port')
                motor = data.get('motor')

                if not port or motor not in [0, 1]:
                    self.send(text_data=json.dumps({
                        'success': False,
                        'error': 'Valid port and motor (0=left, 1=right) required'
                    }))
                    return

                # Create Arduino instance for this motor
                arduino = ArduinoController(port=port, baudrate=9600)

                if arduino.is_connected():
                    self.motors[motor] = arduino
                    self.send(text_data=json.dumps({
                        'success': True,
                        'action': 'connect',
                        'motor': motor,
                        'port': port
                    }))
                    logger.info(f"Motor {motor} connected on {port}")
                else:
                    self.send(text_data=json.dumps({
                        'success': False,
                        'error': f'Failed to connect to {port}'
                    }))

            elif action == 'command':
                motor = data.get('motor')
                command = data.get('command')

                if motor not in self.motors:
                    self.send(text_data=json.dumps({
                        'success': False,
                        'error': f'Motor {motor} not connected'
                    }))
                    return

                if not command:
                    self.send(text_data=json.dumps({
                        'success': False,
                        'error': 'Command is required'
                    }))
                    return

                success = self.motors[motor].send_manual_command(command)

                if success:
                    self.send(text_data=json.dumps({
                        'success': True,
                        'action': 'command',
                        'motor': motor,
                        'command': command
                    }))
                else:
                    self.send(text_data=json.dumps({
                        'success': False,
                        'error': 'Failed to send command'
                    }))

            elif action == 'start':
                # Start Assetto Corsa physics monitoring
                # Check environment variable for required number of motors
                required_motors_env = os.getenv('NUMBER_OF_MOTORS')

                if required_motors_env:
                    required_motors = int(required_motors_env)
                    if len(self.motors) != required_motors:
                        self.send(text_data=json.dumps({
                            'success': False,
                            'action': 'start',
                            'error': f'Required {required_motors} motors, but {len(self.motors)} connected.'
                        }))
                        return
                elif not self.motors:
                    self.send(text_data=json.dumps({
                        'success': False,
                        'action': 'start',
                        'error': 'No motors connected. Connect motors first.'
                    }))
                    return

                # Validate all motor instances
                for motor_num, motor in self.motors.items():
                    if not isinstance(motor, ArduinoController):
                        self.send(text_data=json.dumps({
                            'success': False,
                            'action': 'start',
                            'error': f'Motor {motor_num} is not a valid ArduinoController instance'
                        }))
                        return
                    elif motor.motor_number is None:
                        motor.set_motor_number(motor_num)

                    if not motor.is_connected():
                        self.send(text_data=json.dumps({
                            'success': False,
                            'action': 'start',
                            'error': f'Motor {motor_num} is not connected to Arduino'
                        }))
                        return

                
                # Get primary motor controller (use motor 1 if available, else first available)
                primary_motor = self.motors[1]
                primary_motor.send_command(200,90)


                # Create physics instance with primary motor
                self.ac_physics = AssettoPhysics(arduino_controller=primary_motor)

                # Start monitoring in background thread
                self.monitoring_thread = threading.Thread(
                    target=self.ac_physics.start_monitoring,
                    daemon=True
                )
                self.monitoring_thread.start()

                self.send(text_data=json.dumps({
                    'success': True,
                    'action': 'start',
                    'message': 'Physics monitoring started'
                }))
                logger.info('Assetto Corsa physics monitoring started')
                

            else:
                self.send(text_data=json.dumps({
                    'success': False,
                    'error': 'Invalid action. Use "connect", "command", or "start"'
                }))

        except json.JSONDecodeError:
            self.send(text_data=json.dumps({
                'success': False,
                'error': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error in receive: {e}")
            self.send(text_data=json.dumps({
                'success': False,
                'error': str(e)
            }))


class AvailablePortsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for streaming available Arduino ports.
    Sends port updates every 2 seconds.
    """

    async def connect(self):
        """Accept WebSocket connection and start streaming."""
        await self.accept()
        self.keep_streaming = True
        logger.info("Available ports WebSocket connected")

        # Start streaming available ports
        asyncio.create_task(self.stream_ports())

    async def disconnect(self, close_code):
        """Stop streaming on disconnect."""
        self.keep_streaming = False
        logger.info(f"Available ports WebSocket disconnected: {close_code}")

    async def stream_ports(self):
        """Stream available ports every 2 seconds."""
        while self.keep_streaming:
            try:
                # Get available ports (sync function, run in thread)
                ports = await asyncio.to_thread(ArduinoController.get_available_ports)

                await self.send(text_data=json.dumps({
                    'ports': ports,
                    'count': len(ports)
                }))

                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error streaming ports: {e}")
                break

    async def receive(self, text_data):
        """Handle incoming messages (not used, but required)."""
        pass