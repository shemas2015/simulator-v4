"""DCS World telemetry reader and motor displacement calculator."""

import time
import os
import math
from typing import Dict, Optional
from motion_control.arduino_controller import ArduinoController


class DcsWorldTelemetry:
    """Reads DCS World telemetry and calculates motor angles."""

    def __init__(self, motors: Optional[Dict[int, ArduinoController]] = None):
        """
        Initialize with motor controllers and configuration parameters.

        Args:
            motors: Dict with motor instances {0: left_motor, 1: right_motor}
        """
        self.motors = motors or {}
        self.config = {
            'telemetry_file': os.path.expanduser("~/Saved Games/DCS/telemetry.txt"),  # DCS telemetry data file path
            'rear_x': -1.25,  # Rear fix point position in meters
            'left_motor_y': -0.50,  # Left motor Y position in meters
            'right_motor_y': 0.50,  # Right motor Y position in meters
            'input_min': -1.0,  # Minimum displacement input before rescaling
            'input_max': 1.0,  # Maximum displacement input before rescaling
            'output_min': -0.20,  # Minimum platform displacement in meters
            'output_max': 0.20,  # Maximum platform displacement in meters
            'scale_factor': 90 / 0.25,  # Degrees per meter (90° rotation / 0.25m max height)
        }


    def _calculate_motor_displacement(self, pitch_degrees, roll_degrees):
        """Calculate absolute vertical displacement (D) in meters for each rear motor."""
        pitch_rad = math.radians(pitch_degrees)
        roll_rad = math.radians(roll_degrees)

        tan_pitch = math.tan(pitch_rad)
        tan_roll = math.tan(roll_rad)

        # D = (x * tan(pitch)) - (y * tan(roll))
        left_displacement = (self.config['rear_x'] * tan_pitch) - (self.config['left_motor_y'] * tan_roll)
        right_displacement = (self.config['rear_x'] * tan_pitch) - (self.config['right_motor_y'] * tan_roll)

        # Rescale to valid output values
        left_displacement = self._rescale(left_displacement)
        right_displacement = self._rescale(right_displacement)

        return {'left': left_displacement, 'right': right_displacement}

    def _rescale(self, value):
        """Rescale value from input range to output range with clamping."""
        if value >= self.config['input_max']:
            return self.config['output_max']
        if value <= self.config['input_min']:
            return self.config['output_min']

        # Linear interpolation
        return (value - self.config['input_min']) * (self.config['output_max'] - self.config['output_min']) / \
               (self.config['input_max'] - self.config['input_min']) + self.config['output_min']

    def _calculate_motor_angles(self, left_displacement, right_displacement):
        """Convert displacements to motor angles in degrees (0� = lowest, 90� = rest, 180� = highest)."""
        # Separate pitch and roll movements
        pitch_displacement = (left_displacement + right_displacement) / 2
        roll_displacement = (right_displacement - left_displacement) / 2

        # Calculate theoretical angles
        base_angle = 90.0 + (pitch_displacement * self.config['scale_factor'])
        delta_angle_roll = roll_displacement * self.config['scale_factor']

        left_angle = base_angle - delta_angle_roll
        right_angle = base_angle + delta_angle_roll

        return {'left': left_angle, 'right': right_angle}

    def start_monitoring(self):
        """Monitor DCS telemetry file and calculate motor positions in real-time."""
        last_mtime = 0
        telemetry_file = self.config['telemetry_file']

        while True:
            try:
                if os.path.exists(telemetry_file):
                    mtime = os.path.getmtime(telemetry_file)
                    if mtime != last_mtime:
                        last_mtime = mtime
                        with open(telemetry_file, 'r') as f:
                            data = f.read().strip()
                        if data:
                            values = data.split(",")
                            pitch = float(values[0])
                            roll = float(values[1])

                            displacements = self._calculate_motor_displacement(pitch, roll)
                            left_d = displacements['left']
                            right_d = displacements['right']

                            angles = self._calculate_motor_angles(left_d, right_d)
                            left_angle = angles['left']
                            right_angle = angles['right']

                            # Clear screen
                            os.system('cls' if os.name == 'nt' else 'clear')

                            # Send commands to motors
                        
                            self.motors[1].send_command(speed=100, angle=int(right_angle), verbose=False)
                            self.motors[0].send_command(speed=100, angle=int(left_angle), verbose=False)



                else:
                    print("Waiting for DCS data...", end="\r")
                time.sleep(0.05)
            except KeyboardInterrupt:
                print("\nStopped.")
                break
            except Exception as e:
                print(f"Error: {e}", end="\r")
                time.sleep(0.1)
