import threading
import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Singleton class to manage Arduino motor connections state.
    Tracks connection status for multiple motors and notifies listeners.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._connections: Dict[str, Dict[str, Any]] = {}
        self._listeners = []
        self._data_lock = threading.Lock()

        logger.info("ConnectionManager initialized")

    def register_connection(self, port: str, motor_number: int = None) -> None:
        """
        Register a new Arduino connection.

        Args:
            port: Serial port (e.g., COM3, /dev/ttyUSB0)
            motor_number: Optional motor number (1 or 2)
        """
        with self._data_lock:
            self._connections[port] = {
                'port': port,
                'connected': True,
                'motor_number': motor_number,
                'position': None,  # 'left' or 'right'
                'connected_at': datetime.now().isoformat(),
                'last_command': None,
            }

        logger.info(f"Registered connection on {port} (motor {motor_number})")
        self._notify_listeners()

    def unregister_connection(self, port: str) -> None:
        """
        Unregister an Arduino connection.

        Args:
            port: Serial port
        """
        with self._data_lock:
            if port in self._connections:
                del self._connections[port]

        logger.info(f"Unregistered connection on {port}")
        self._notify_listeners()

    def update_connection_status(self, port: str, connected: bool) -> None:
        """
        Update connection status for a port.

        Args:
            port: Serial port
            connected: Connection status
        """
        with self._data_lock:
            if port in self._connections:
                self._connections[port]['connected'] = connected
                if not connected:
                    self._connections[port]['disconnected_at'] = datetime.now().isoformat()

        logger.info(f"Updated connection status for {port}: {connected}")
        self._notify_listeners()

    def update_motor_position(self, port: str, position: str) -> None:
        """
        Update motor position (left/right).

        Args:
            port: Serial port
            position: 'left' or 'right'
        """
        with self._data_lock:
            if port in self._connections:
                self._connections[port]['position'] = position

        logger.info(f"Updated motor position for {port}: {position}")
        self._notify_listeners()

    def update_last_command(self, port: str, command: Dict[str, Any]) -> None:
        """
        Update last command sent to motor.

        Args:
            port: Serial port
            command: Command data (speed, angle, etc.)
        """
        with self._data_lock:
            if port in self._connections:
                self._connections[port]['last_command'] = command
                self._connections[port]['last_command_at'] = datetime.now().isoformat()

    def get_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered connections.

        Returns:
            Dictionary of all connections
        """
        with self._data_lock:
            return dict(self._connections)

    def get_connection(self, port: str) -> Optional[Dict[str, Any]]:
        """
        Get connection info for a specific port.

        Args:
            port: Serial port

        Returns:
            Connection info or None
        """
        with self._data_lock:
            return self._connections.get(port)

    def add_listener(self, callback) -> None:
        """
        Add a listener to be notified of connection changes.

        Args:
            callback: Function to call on connection changes
        """
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback) -> None:
        """
        Remove a listener.

        Args:
            callback: Function to remove
        """
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self) -> None:
        """Notify all registered listeners of connection changes."""
        for listener in self._listeners:
            try:
                listener(self.get_all_connections())
            except Exception as e:
                logger.error(f"Error notifying listener: {e}")


# Global instance
connection_manager = ConnectionManager()
