"""
Assetto Corsa Simulator - Writes fake data to shared memory
Simulates AC physics data for testing without running the actual game
"""
import mmap
import ctypes
import time
import math
import random
from sim_info import SPageFilePhysics, SPageFileGraphic, SPageFileStatic

class ACSimulator:
    def __init__(self):
        # Create shared memory mappings (same names as AC uses)
        try:
            self._physics_mm = mmap.mmap(0, ctypes.sizeof(SPageFilePhysics), "acpmf_physics")
            self._graphics_mm = mmap.mmap(0, ctypes.sizeof(SPageFileGraphic), "acpmf_graphics")
            self._static_mm = mmap.mmap(0, ctypes.sizeof(SPageFileStatic), "acpmf_static")
        except Exception as e:
            print(f"Error creating shared memory: {e}")
            return

        # Create structures
        self.physics = SPageFilePhysics.from_buffer(self._physics_mm)
        self.graphics = SPageFileGraphic.from_buffer(self._graphics_mm)
        self.static = SPageFileStatic.from_buffer(self._static_mm)

        # Initialize static data (car/track info)
        self._init_static_data()

        # Simulation state
        self.time_elapsed = 0
        self.speed = 0
        self.gear = 1
        self.rpm = 1000

    def _init_static_data(self):
        """Initialize static car and track data"""
        self.static.carModel = "BMW M3 E30"
        self.static.track = "Nurburgring"
        self.static.playerName = "Test"
        self.static.playerSurname = "Driver"
        self.static.playerNick = "TestDriver"
        self.static.maxRpm = 7000
        self.static.maxTorque = 400.0
        self.static.maxPower = 300.0
        self.static.maxFuel = 60.0

    def simulate_driving(self):
        """Simulate realistic driving physics"""
        # Simulate acceleration/deceleration
        target_speed = random.uniform(50, 200)  # km/h

        if self.speed < target_speed:
            self.speed += random.uniform(1, 5)
        else:
            self.speed -= random.uniform(1, 3)

        self.speed = max(0, min(self.speed, 250))  # Clamp speed

        # Simulate gear changes with more realistic thresholds
        old_gear = self.gear

        # Upshift conditions
        if self.gear == 1 and self.speed > 20:
            if random.random() < 0.15:  # Higher chance at low gears
                self.gear = 2
        elif self.gear == 2 and self.speed > 40:
            if random.random() < 0.12:
                self.gear = 3
        elif self.gear == 3 and self.speed > 70:
            if random.random() < 0.10:
                self.gear = 4
        elif self.gear == 4 and self.speed > 100:
            if random.random() < 0.08:
                self.gear = 5
        elif self.gear == 5 and self.speed > 140:
            if random.random() < 0.06:
                self.gear = 6

        # Downshift conditions
        elif self.gear == 6 and self.speed < 120:
            if random.random() < 0.08:
                self.gear = 5
        elif self.gear == 5 and self.speed < 80:
            if random.random() < 0.10:
                self.gear = 4
        elif self.gear == 4 and self.speed < 50:
            if random.random() < 0.12:
                self.gear = 3
        elif self.gear == 3 and self.speed < 25:
            if random.random() < 0.15:
                self.gear = 2
        elif self.gear == 2 and self.speed < 10:
            if random.random() < 0.20:
                self.gear = 1

        # Print gear changes for visibility
        if old_gear != self.gear:
            change_type = "UPSHIFT" if self.gear > old_gear else "DOWNSHIFT"
            print(f"  {change_type}: {old_gear} -> {self.gear} (Speed: {self.speed:.1f} km/h)")

        # RPM based on speed and gear
        self.rpm = int(1000 + (self.speed * 50 / self.gear))
        self.rpm = min(self.rpm, 7000)

    def update_physics(self):
        """Update physics data in shared memory"""
        self.simulate_driving()

        # Basic physics
        self.physics.speedKmh = self.speed
        self.physics.gear = self.gear
        self.physics.rpms = self.rpm
        self.physics.gas = random.uniform(0.3, 1.0) if self.speed < 180 else random.uniform(0.1, 0.5)
        self.physics.brake = random.uniform(0.0, 0.3) if self.speed > 100 else 0.0

        # Simulate pitch and roll (car body movement)
        self.physics.pitch = math.sin(self.time_elapsed * 0.5) * 0.1  # Small pitch changes
        self.physics.roll = math.sin(self.time_elapsed * 0.8) * 0.05   # Small roll changes

        # Acceleration G-forces
        accel_factor = (self.physics.gas - self.physics.brake) * 2
        self.physics.accG[0] = random.uniform(-0.5, 0.5)  # Lateral
        self.physics.accG[1] = random.uniform(-0.2, 0.2)  # Vertical
        self.physics.accG[2] = accel_factor + random.uniform(-0.3, 0.3)  # Longitudinal

        # Steering angle
        self.physics.steerAngle = math.sin(self.time_elapsed * 0.3) * 0.2

        # Fuel consumption
        self.physics.fuel = max(0, 50 - (self.time_elapsed * 0.1))

    def update_graphics(self):
        """Update graphics/session data"""
        # Session info
        self.graphics.status = 2  # AC_LIVE
        self.graphics.session = 0  # AC_PRACTICE

        # Lap timing (fake times)
        minutes = int(self.time_elapsed // 60)
        seconds = int(self.time_elapsed % 60)
        milliseconds = int((self.time_elapsed * 1000) % 1000)
        self.graphics.currentTime = f"{minutes:02d}:{seconds:02d}:{milliseconds:03d}"

        self.graphics.completedLaps = int(self.time_elapsed // 120)  # 2-minute laps
        self.graphics.position = 1
        self.graphics.isInPit = 0

    def run_simulation(self, duration=None):
        """Run the simulation loop"""
        print("Starting Assetto Corsa simulation...")
        print("Other applications can now read from shared memory")
        print("Press Ctrl+C to stop")

        start_time = time.time()

        try:
            while True:
                current_time = time.time()
                self.time_elapsed = current_time - start_time

                # Stop if duration specified
                if duration and self.time_elapsed >= duration:
                    break

                # Update simulation data
                self.update_physics()
                self.update_graphics()

                # Print status every 2 seconds
                if int(self.time_elapsed) % 2 == 0 and self.time_elapsed % 1 < 0.1:
                    print(f"Speed: {self.physics.speedKmh:.1f} km/h | "
                          f"Gear: {self.physics.gear} | "
                          f"RPM: {self.physics.rpms} | "
                          f"Time: {self.graphics.currentTime}")

                time.sleep(0.05)  # 20 FPS update rate

        except KeyboardInterrupt:
            print("\nSimulation stopped by user")

    def close(self):
        """Clean up shared memory"""
        self._physics_mm.close()
        self._graphics_mm.close()
        self._static_mm.close()

    def __del__(self):
        self.close()

if __name__ == "__main__":
    simulator = ACSimulator()
    simulator.run_simulation()