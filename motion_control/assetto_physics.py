import time
import os
import math
import logging
from sim_info import info


class AssettoPhysics:
    """
    Simple class to read Assetto Corsa physics data.
    Based on the original asseto_physics.py functionality.
    """

    def __init__(self, arduino_controller):
        """
        Initialize connection to Assetto Corsa.
        
        Args:
            arduino_controller: ArduinoController instance for motor control (required)
        """
        if arduino_controller is None:
            raise ValueError("arduino_controller parameter is required and cannot be None")
        
        self.info = info
        self.previous_z_accel = None
        self.previous_gear = None
        self.arduino_controller = arduino_controller
        self.logger = logging.getLogger('arduino_control')


    def _get_physics(self):
        phys = self.info.physics
        data = {}
        
        for name, _ in phys._fields_:
            try:
                data[name] = getattr(phys, name)
            except Exception:
                data[name] = None
    
        return data

    
    def start_monitoring(self):
        last_gear = 1
        last_acc_long = None
        last_gas = 0.0

        while True:
            physics_info = self._get_physics()
            gas = round(physics_info["gas"], 2)

            # Detect accelerator pedal press
            if last_gas == 0.0 and gas > 0.1:
                self.arduino_controller.send_command(200,100)
                self.arduino_controller.send_command(200,90)
            last_gas = gas



