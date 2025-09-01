from django.core.management.base import BaseCommand, CommandError
from motion_control.arduino_controller import ArduinoController


class Command(BaseCommand):
    help = 'Control Arduino motor via serial communication'

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
            # Create Arduino controller with specified options
            arduino = ArduinoController(
                baudrate=options['baudrate']
            )
            
            # Connect to Arduino
            if not arduino.connect(options['port']):
                return

            # Start interactive mode
            arduino.interactive_mode()

        except Exception as e:
            raise CommandError(f'Command failed: {e}')
        
        finally:
            # Arduino controller handles cleanup automatically via context manager
            pass