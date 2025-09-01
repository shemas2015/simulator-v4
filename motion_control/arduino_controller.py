import serial
import serial.tools.list_ports
import time
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class ArduinoController:
    """
    Custom class to handle all Arduino serial communication and motor control.
    Manages connection, command sending, and response handling.
    """

    def __init__(self, baudrate: int = 9600, timeout: float = 1.0):
        """
        Initialize Arduino controller.
        
        Args:
            baudrate: Serial communication baud rate
            timeout: Serial communication timeout in seconds
        """
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection: Optional[serial.Serial] = None
        self.port: Optional[str] = None
        self._is_connected = False

    def get_available_ports(self) -> List[Dict[str, str]]:
        """
        Get list of available USB/serial ports that could be Arduino devices.
        
        Returns:
            List of dictionaries with port information
        """
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
        
        return available_ports

    def list_ports(self) -> None:
        """Print available ports to console."""
        ports = self.get_available_ports()
        
        if not ports:
            print("No USB/Serial devices found. Make sure Arduino is connected.")
            return

        print("\nAvailable USB/Serial devices:")
        print("-" * 50)
        
        for idx, port in enumerate(ports):
            print(f"{idx + 1}. {port['device']} - {port['description']}")

    def select_port_interactive(self) -> Optional[str]:
        """
        Interactive port selection from available devices.
        
        Returns:
            Selected port device path or None if cancelled
        """
        ports = self.get_available_ports()
        
        if not ports:
            print("No USB/Serial devices found. Make sure Arduino is connected.")
            return None

        print("\nAvailable USB/Serial devices:")
        print("-" * 50)
        
        for idx, port in enumerate(ports):
            print(f"{idx + 1}. {port['device']} - {port['description']}")
        
        while True:
            try:
                choice = input("\nSelect device number (or 'q' to quit): ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(ports):
                    return ports[choice_idx]['device']
                else:
                    print("Invalid selection. Please try again.")
            
            except (ValueError, KeyboardInterrupt):
                print("\nOperation cancelled.")
                return None

    def connect(self, port: Optional[str] = None) -> bool:
        """
        Connect to Arduino on specified port.
        
        Args:
            port: Serial port path. If None, will prompt for selection
            
        Returns:
            True if connection successful, False otherwise
        """
        if port is None:
            port = self.select_port_interactive()
        
        if not port:
            return False

        try:
            self.connection = serial.Serial(port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # Wait for Arduino to reset
            
            self.port = port
            self._is_connected = True
            
            logger.info(f"Connected to Arduino on {port} at {self.baudrate} baud")
            print(f"✓ Connected to Arduino on {port} at {self.baudrate} baud")
            return True
            
        except serial.SerialException as e:
            logger.error(f"Failed to connect to {port}: {e}")
            print(f"✗ Failed to connect to {port}: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Arduino."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("✓ Serial connection closed.")
        
        self._is_connected = False
        self.connection = None
        self.port = None

    def is_connected(self) -> bool:
        """
        Check if Arduino is connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self._is_connected and self.connection and self.connection.is_open

    def send_command(self, speed: int, angle: int, verbose: bool = True) -> bool:
        """
        Send speed,angle command to Arduino.
        
        Args:
            speed: Motor speed (0-255)
            angle: Servo angle (0-180)
            verbose: Print command details
            
        Returns:
            True if command sent successfully, False otherwise
        """
        if not self.is_connected():
            logger.error("No active connection to Arduino")
            if verbose:
                print("✗ No active connection to Arduino")
            return False

        # Validate ranges
        if not (0 <= speed <= 255):
            logger.error(f"Invalid speed: {speed}. Must be between 0-255")
            if verbose:
                print(f"✗ Invalid speed: {speed}. Must be between 0-255")
            return False
        
        if not (0 <= angle <= 180):
            logger.error(f"Invalid angle: {angle}. Must be between 0-180")
            if verbose:
                print(f"✗ Invalid angle: {angle}. Must be between 0-180")
            return False

        try:
            command = f"{speed},{angle}\n"
            self.connection.write(command.encode())
            
            if verbose:
                logger.info(f"Sent command: Speed={speed}, Angle={angle}")
                print(f"✓ Sent command: Speed={speed}, Angle={angle}")
            
            # Try to read response from Arduino
            response = self.read_response()
            if response and verbose:
                print(f"Arduino response: {response}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            if verbose:
                print(f"✗ Error sending command: {e}")
            return False

    def read_response(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Read response from Arduino.
        
        Args:
            timeout: Read timeout in seconds. If None, uses default
            
        Returns:
            Response string or None if no response/error
        """
        if not self.is_connected():
            return None

        try:
            old_timeout = self.connection.timeout
            if timeout is not None:
                self.connection.timeout = timeout
            
            time.sleep(0.1)  # Give Arduino time to respond
            
            if self.connection.in_waiting > 0:
                try:
                    response = self.connection.readline().decode('utf-8', errors='ignore').strip()
                    return response if response else None
                except Exception:
                    # If decoding fails, try reading raw bytes
                    raw_response = self.connection.readline()
                    return f"Raw: {raw_response}"
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading response: {e}")
            return None
        finally:
            if timeout is not None:
                self.connection.timeout = old_timeout

    def send_raw_command(self, command: str, verbose: bool = True) -> bool:
        """
        Send raw string command to Arduino.
        
        Args:
            command: Raw command string
            verbose: Print command details
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_connected():
            if verbose:
                print("✗ No active connection to Arduino")
            return False

        try:
            if not command.endswith('\n'):
                command += '\n'
                
            self.connection.write(command.encode())
            
            if verbose:
                logger.info(f"Sent raw command: {command.strip()}")
                print(f"✓ Sent raw command: {command.strip()}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending raw command: {e}")
            if verbose:
                print(f"✗ Error sending raw command: {e}")
            return False

    def test_connection(self) -> bool:
        """
        Test Arduino connection by sending a test command.
        
        Returns:
            True if test successful, False otherwise
        """
        if not self.is_connected():
            print("✗ Not connected to Arduino")
            return False

        print("Testing connection...")
        
        # Send a neutral position command as test
        success = self.send_command(0, 90, verbose=False)
        
        if success:
            print("✓ Connection test successful")
            return True
        else:
            print("✗ Connection test failed")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get current controller status.
        
        Returns:
            Dictionary with status information
        """
        return {
            'connected': self.is_connected(),
            'port': self.port,
            'baudrate': self.baudrate,
            'timeout': self.timeout,
            'available_ports': len(self.get_available_ports())
        }

    def print_status(self) -> None:
        """Print current status to console."""
        status = self.get_status()
        
        print("\n--- Arduino Controller Status ---")
        print(f"Connected: {'✓ Yes' if status['connected'] else '✗ No'}")
        
        if status['connected']:
            print(f"Port: {status['port']}")
            print(f"Baud rate: {status['baudrate']}")
            print(f"Timeout: {status['timeout']}s")
        
        print(f"Available ports: {status['available_ports']}")
        print("--------------------------------\n")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def interactive_mode(self):
        """
        Start interactive command input mode for Arduino control.
        Allows user to send speed,angle commands interactively.
        """
        if not self.is_connected():
            print("✗ Not connected to Arduino. Cannot start interactive mode.")
            return

        print("\n✓ Interactive mode started. Enter commands as: speed,angle")
        print("Examples: 100,90 or 50,45")
        print("Type 'quit', 'exit', or 'q' to stop")
        print("Type 'status' to show connection status")
        print("Type 'test' to test connection\n")

        while True:
            try:
                user_input = input("Enter command: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'status':
                    self.print_status()
                    continue
                elif user_input.lower() == 'test':
                    self.test_connection()
                    continue
                
                # Parse speed,angle input
                try:
                    parts = user_input.split(',')
                    if len(parts) != 2:
                        raise ValueError("Invalid format")
                    
                    speed = int(parts[0].strip())
                    angle = int(parts[1].strip())
                    
                    # Send command (validation is handled in send_command)
                    self.send_command(speed, angle)
                    
                except ValueError:
                    print("✗ Invalid format. Use: speed,angle (e.g., 100,90)")
                    continue
                except Exception as e:
                    print(f"✗ Unexpected error: {e}")
                    continue
                    
            except KeyboardInterrupt:
                break

        print("\n✓ Exiting interactive mode...")

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.disconnect()
        except Exception:
            pass