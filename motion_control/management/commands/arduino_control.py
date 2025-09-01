import serial
import serial.tools.list_ports
import time
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Control Arduino motor via serial communication'

    def __init__(self):
        super().__init__()
        self.connection = None

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

    def get_available_ports(self):
        """Get list of available USB/serial ports"""
        ports = serial.tools.list_ports.comports()
        available_ports = []
        
        for port in ports:
            # Filter for likely Arduino ports
            if any(keyword in port.description.lower() for keyword in ['arduino', 'usb', 'serial']):
                available_ports.append({
                    'device': port.device,
                    'description': port.description,
                    'hwid': port.hwid
                })
        
        return available_ports

    def select_port(self):
        """Display available ports and let user choose"""
        ports = self.get_available_ports()
        
        if not ports:
            self.stdout.write(
                self.style.ERROR('No USB/Serial devices found. Make sure Arduino is connected.')
            )
            return None

        self.stdout.write(self.style.SUCCESS('\nAvailable USB/Serial devices:'))
        self.stdout.write('-' * 50)
        
        for idx, port in enumerate(ports):
            self.stdout.write(f"{idx + 1}. {port['device']} - {port['description']}")
        
        while True:
            try:
                choice = input("\nSelect device number (or 'q' to quit): ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(ports):
                    return ports[choice_idx]['device']
                else:
                    self.stdout.write(self.style.ERROR('Invalid selection. Please try again.'))
            
            except (ValueError, KeyboardInterrupt):
                self.stdout.write(self.style.ERROR('\nOperation cancelled.'))
                return None

    def connect_to_arduino(self, port, baudrate):
        """Establish serial connection to Arduino"""
        try:
            self.connection = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            
            self.stdout.write(
                self.style.SUCCESS(f'Connected to Arduino on {port} at {baudrate} baud')
            )
            return True
            
        except serial.SerialException as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to connect to {port}: {e}')
            )
            return False

    def send_command(self, speed, angle):
        """Send speed,angle command to Arduino"""
        if not self.connection or not self.connection.is_open:
            self.stdout.write(self.style.ERROR('No active connection to Arduino'))
            return False

        try:
            command = f"{speed},{angle}\n"
            self.connection.write(command.encode())
            
            self.stdout.write(
                self.style.SUCCESS(f'Sent command: Speed={speed}, Angle={angle}')
            )
            
            # Try to read response from Arduino
            time.sleep(0.1)
            if self.connection.in_waiting > 0:
                try:
                    response = self.connection.readline().decode('utf-8', errors='ignore').strip()
                    if response:
                        self.stdout.write(f'Arduino response: {response}')
                except Exception:
                    # If decoding fails, show raw bytes
                    raw_response = self.connection.readline()
                    self.stdout.write(f'Arduino raw response: {raw_response}')
            
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending command: {e}')
            )
            return False

    def interactive_mode(self):
        """Interactive command input mode"""
        self.stdout.write(
            self.style.SUCCESS('\nInteractive mode started. Enter commands as: speed,angle')
        )
        self.stdout.write('Examples: 100,90 or 50,45')
        self.stdout.write("Type 'quit' or 'exit' to stop\n")

        while True:
            try:
                user_input = input("Enter command (speed,angle): ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                # Parse speed,angle input
                try:
                    parts = user_input.split(',')
                    if len(parts) != 2:
                        raise ValueError("Invalid format")
                    
                    speed = int(parts[0].strip())
                    angle = int(parts[1].strip())
                    
                    # Validate ranges
                    if not (0 <= speed <= 255):
                        self.stdout.write(self.style.ERROR('Speed must be between 0-255'))
                        continue
                    
                    if not (0 <= angle <= 180):
                        self.stdout.write(self.style.ERROR('Angle must be between 0-180'))
                        continue
                    
                    self.send_command(speed, angle)
                    
                except ValueError:
                    self.stdout.write(
                        self.style.ERROR('Invalid format. Use: speed,angle (e.g., 100,90)')
                    )
                    continue
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Unexpected error: {e}')
                    )
                    continue
                    
            except KeyboardInterrupt:
                break

        self.stdout.write(self.style.SUCCESS('\nExiting interactive mode...'))

    def handle(self, *args, **options):
        try:
            # Select port
            if options['port']:
                selected_port = options['port']
            else:
                selected_port = self.select_port()
            
            if not selected_port:
                return

            # Connect to Arduino
            if not self.connect_to_arduino(selected_port, options['baudrate']):
                return

            # Start interactive mode
            self.interactive_mode()

        except Exception as e:
            raise CommandError(f'Command failed: {e}')
        
        finally:
            if self.connection and self.connection.is_open:
                self.connection.close()
                self.stdout.write(self.style.SUCCESS('Serial connection closed.'))