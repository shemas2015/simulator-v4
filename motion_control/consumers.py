import json
import logging
import asyncio
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from motion_control.arduino_controller import ArduinoController

logger = logging.getLogger(__name__)


class ArduinoControlConsumer(WebsocketConsumer):
    """
    WebSocket consumer for real-time Arduino motor control.
    Connects to Arduino on initialization, sends f/b commands.
    """

    def connect(self):
        """Accept WebSocket connection and connect to Arduino."""
        # Get port from URL
        self.port = self.scope['url_route']['kwargs']['port']

        # Create Arduino connection
        self.arduino = ArduinoController(port=self.port, baudrate=9600)

        if not self.arduino.is_connected():
            self.close()
            return

        self.accept()
        logger.info(f"WebSocket connected to Arduino on {self.port}")

    def disconnect(self, close_code):
        """Clean up Arduino connection on WebSocket disconnect."""
        if hasattr(self, 'arduino') and self.arduino and self.arduino.is_connected():
            self.arduino.disconnect()
            logger.info(f"Disconnected from Arduino on {self.port}")

    def receive(self, text_data):
        """
        Handle incoming commands.

        Expected message: {"command": "f"} or {"command": "b"}
        """
        try:
            data = json.loads(text_data)
            command = data.get('command')

            if not command:
                self.send(text_data=json.dumps({
                    'success': False,
                    'error': 'Command is required'
                }))
                return

            # Send command to Arduino
            success = self.arduino.send_manual_command(command)

            if success:
                self.send(text_data=json.dumps({
                    'success': True,
                    'command': command
                }))
            else:
                self.send(text_data=json.dumps({
                    'success': False,
                    'error': 'Failed to send command'
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