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

    def dump_physics_once(self):
        """Read and print all physics data once."""
        phys = self.info.physics
        
        # Si la estructura tiene _fields_ la usamos para listar todo
        if hasattr(phys, "_fields_"):
            for name, _ in phys._fields_:
                try:
                    print(f"{name}: {getattr(phys, name)}")
                except Exception:
                    print(f"{name}: <error reading>")
        else:
            # fallback: intenta imprimir atributos públicos
            for name in dir(phys):
                if name.startswith("_"): 
                    continue
                try:
                    val = getattr(phys, name)
                    if callable(val): 
                        continue
                    print(f"{name}: {val}")
                except Exception:
                    pass

    def start_monitoring(self, poll_hz=10):
        """
        Start continuous monitoring of physics data.
        
        Args:
            poll_hz: Polling frequency in Hz (default: 10)
        """
        interval = 1.0 / poll_hz
        print("Esperando Assetto Corsa... (Ctrl+C para salir)")
        
        try:
            while True:
                os.system("cls" if os.name == "nt" else "clear")
                print(time.strftime("%Y-%m-%d %H:%M:%S"))
                self.dump_physics_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nDetenido por usuario.")

    def get_physics_data(self):
        """
        Get physics data as a dictionary.
        
        Returns:
            dict: Physics data
        """
        phys = self.info.physics
        data = {}
        
        if hasattr(phys, "_fields_"):
            for name, _ in phys._fields_:
                try:
                    data[name] = getattr(phys, name)
                except Exception:
                    data[name] = None
        else:
            # fallback: intenta obtener atributos públicos
            for name in dir(phys):
                if name.startswith("_"): 
                    continue
                try:
                    val = getattr(phys, name)
                    if callable(val): 
                        continue
                    data[name] = val
                except Exception:
                    pass
        
        return data

    def monitor_pitch_roll(self):
        """Monitor and print pitch, roll and acceleration values in real time loop."""
        print("Starting pitch, roll and acceleration monitoring... (Ctrl+C to stop)")
        
        # Variable to track previous acceleration for sprint factor calculation
        previous_z_accel = None
        
        try:
            while True:
                # Clear screen
                os.system("cls" if os.name == "nt" else "clear")
                
                physics_data = self.get_physics_data()
                if physics_data:
                    # Get pitch and roll directly using the correct field names
                    pitch = physics_data.get('pitch')
                    roll = physics_data.get('roll')
                    accG = physics_data.get('accG')


                    val = physics_data.get('accG')  # example <c_float_Array_3>
                    x, y, z = val[0], val[1], val[2]

                    # Calculate sprint acceleration factor (abrupt acceleration detection)
                    sprint_factor = 0
                    acceleration_status = "Normal"
                    
                    if previous_z_accel is not None:
                        # Calculate the change in acceleration (jerk)
                        accel_change = abs(z - previous_z_accel)
                        
                        # Sprint factor based on acceleration change
                        sprint_factor = accel_change * 10  # Scale factor for visibility
                        
                        print("Aceleration change: " + str(accel_change))
                        """
                        # Determine if acceleration is abrupt
                        if accel_change > 0.5:  # Threshold for abrupt acceleration
                            acceleration_status = "ABRUPT!"
                        elif accel_change > 0.2:
                            acceleration_status = "Moderate"
                        """
                    
                    # Update previous acceleration for next iteration
                    previous_z_accel = z
                    
                    """
                    print("Lateral: "+str(x))
                    print("Vertical: "+str(y)) #(baches, saltos)
                    print("Longitudinal: "+str(z)) # (acelerar/frenar)
                    print(f"Sprint Factor: {sprint_factor:.2f} - {acceleration_status}")
                    """
                    
                    
                    
                    
                    # Print current values
                    print("Pitch and Roll Monitoring:")
                    print("-" * 30)
                    if pitch is not None:
                        pitch_degrees = math.degrees(pitch)
                        print(f'  Pitch: {pitch_degrees:.2f}°')
                    if roll is not None:
                        roll_degrees = math.degrees(roll)
                        print(f'  Roll: {roll_degrees:.2f}°')
                    
                    print(f"\nTime: {time.strftime('%H:%M:%S')}")
                    print("Press Ctrl+C to stop")
                
                time.sleep(0.1)  # Update 10 times per second
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")

    def get_acceleration_factor(self):
        """
        Get current acceleration factor based on longitudinal acceleration change.
        
        Returns:
            dict: Contains acceleration data and factor
                - x: Lateral acceleration 
                - y: Vertical acceleration
                - z: Longitudinal acceleration
                - factor: Sprint acceleration factor
                - change: Acceleration change from previous reading
                - status: Acceleration status (Normal, Moderate, ABRUPT!)
        """
        physics_data = self.get_physics_data()
        
        if not physics_data:
            return None
            
        accG = physics_data.get('accG')
        if not accG:
            return None
            
        # Extract acceleration components
        x, y, z = accG[0], accG[1], accG[2]
        
        # Calculate acceleration factor
        factor = 0
        accel_change = 0
        status = "Normal"
        
        if self.previous_z_accel is not None:
            # Calculate the change in acceleration (jerk)
            accel_change = abs(z - self.previous_z_accel)
            
            # Sprint factor based on acceleration change
            factor = accel_change * 10  # Scale factor for visibility
            
            # Determine acceleration status
            if accel_change > 0.5:  # Threshold for abrupt acceleration
                status = "ABRUPT!"
            elif accel_change > 0.2:
                status = "Moderate"
        
        # Update previous acceleration for next call
        self.previous_z_accel = z
        
        return {
            'x': x,           # Lateral
            'y': y,           # Vertical (bumps, jumps)
            'z': z,           # Longitudinal (accelerate/brake)
            'factor': factor,
            'change': accel_change,
            'status': status
        }

    def get_gear_change(self):
        """
        Detect gear changes and return gear information.
        
        Returns:
            dict: Contains gear data and change status
                - current_gear: Current gear number
                - previous_gear: Previous gear number  
                - gear_changed: Boolean indicating if gear changed
                - change_type: 'up', 'down', or None
                - change_direction: Positive for upshift, negative for downshift
        """
        physics_data = self.get_physics_data()
        
        if not physics_data:
            return None
            
        current_gear = physics_data.get('gear')
        if current_gear is None:
            return None
        
        # Check for gear change
        gear_changed = False
        change_type = None
        change_direction = 0
        
        if self.previous_gear is not None and self.previous_gear != current_gear:
            gear_changed = True
            change_direction = current_gear - self.previous_gear
            
            if change_direction > 0:
                change_type = 'up'
            elif change_direction < 0:
                change_type = 'down'
        
        # Store current gear for next comparison
        previous_gear = self.previous_gear
        self.previous_gear = current_gear
        
        return {
            'current_gear': current_gear,
            'previous_gear': previous_gear,
            'gear_changed': gear_changed,
            'change_type': change_type,
            'change_direction': change_direction
        }

    def monitor_gear_changes(self):
        """Monitor gear changes in a continuous loop with logging."""
        logger = logging.getLogger('arduino_control')
        logger.info('Starting gear change monitoring...')
        try:
            while True:
                gear_data = self.get_gear_change()
                
                if gear_data and gear_data['gear_changed']:
                    # Get current acceleration factor when gear changes
                    accel_data = self.get_acceleration_factor()
                    accel_info = ""
                    if accel_data:
                        accel_info = f" | Accel Factor: {accel_data['factor']:.2f} ({accel_data['status']})"
                    
                    logger.info(f"Gear change detected: {gear_data['previous_gear']} -> {gear_data['current_gear']} ({gear_data['change_type']}shift){accel_info}")
                    
                    # Check for upshift with abrupt acceleration
                    if gear_data['change_type'] == 'up' and accel_data and accel_data['status'] == 'ABRUPT!':
                        logger.info("MOVER MOTOR - Upshift with abrupt acceleration detected!")
                        self.arduino_controller.send_command(speed=100, angle=105)
                    
                    # Add your gear change logic here
                    # Example: Trigger Arduino commands based on gear changes
                
                time.sleep(0.05)  # Check gear changes 20 times per second
                
        except Exception as e:
            logger.error(f"Gear monitoring error: {e}")