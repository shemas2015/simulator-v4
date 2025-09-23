from django.core.management.base import BaseCommand, CommandError
from motion_control.arduino_controller import ArduinoController
from motion_control.assetto_physics import AssettoPhysics
import threading
import time
import logging
import serial.tools.list_ports


class Command(BaseCommand):
    help = 'Control Arduino motor via serial communication'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('arduino_control')

    def add_arguments(self, parser):
        parser.add_argument(
            '--port',
            type=str,
            help='Specify the serial port directly (e.g., COM3)'
        )
        parser.add_argument(
            '--baudrate',
            type=int,
            default=9600,
            help='Serial communication baud rate (default: 9600)'
        )

    def handle(self, *args, **options):
        try:
            # Check if port is provided
            if not options['port']:
                # Get available ports without creating instance
                #available_ports = ArduinoController.get_available_ports()
                ports = serial.tools.list_ports.comports()
                available_ports = []
                
                for port in ports:
                    # Filter for likely Arduino ports
                    if any(keyword in port.description.lower() for keyword in ['arduino', 'usb', 'serial', 'ch340', 'cp2102']):
                        available_ports.append({
                            'device': port.device,
                            'description': port.description,
                            'hwid': port.hwid
                        })

                self.logger.error('Port parameter is required')
                self.logger.info('Available COM ports:')
                if available_ports:
                    for port in available_ports:
                        self.logger.info(f"  {port['device']} - {port['description']}")
                    # Show example with first available port
                    first_port = available_ports[0]['device']
                    self.logger.info(f"Example: python manage.py arduino_control --port {first_port}")
                else:
                    self.logger.info('  No Arduino/USB Serial devices found')
                return
            
            # Connect to Assetto Corsa and start pitch/roll monitoring
            
            
            """
            # Start monitoring in background thread
            monitor_thread = threading.Thread(
                target=ac_physics.monitor_pitch_roll, 
                daemon=True
            )
            monitor_thread.start()
            self.logger.info('Physics monitoring started in background')
            """
            
            # Create Arduino controller with specified options
            arduino = ArduinoController(
                port=options['port'],
                baudrate=options['baudrate']
            )

            self.logger.info('Connecting to Assetto Corsa...')
            ac_physics = AssettoPhysics(arduino_controller=arduino)
            
            # Check Arduino connection status (already attempted in constructor)
            if not arduino._is_connected:
                self.logger.error(f"Failed to connect to Arduino on port {options['port']}")
                return

            arduino.send_command(100,90)
            # Start gear monitoring in background thread
            gear_thread = threading.Thread(
                target=ac_physics.monitor_gear_changes,
                daemon=True
            )
            gear_thread.start()
            self.logger.info('Gear change monitoring started in background')
            
            # TODO: Add other physics event checks here before starting main functionality
            # Example: Check for specific conditions, initialize other systems, etc.
            self.logger.warning('Ready for additional physics event checks...')
            
            # Keep main thread alive to allow background monitoring
            try:
                while True:
                    time.sleep(1)  # Keep main thread running
                    
            except KeyboardInterrupt:
                self.logger.info('Shutting down...')

            # Commented Arduino code (keep for later use)
            

        except Exception as e:
            raise CommandError(f'Command failed: {e}')
        
        finally:
            pass