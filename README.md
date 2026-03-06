# Motion Control Simulator

A Django-based motion control simulator with hardware integration for Arduino motor control and Assetto Corsa physics monitoring.

## Project Overview

This project provides a web interface and control system for motor simulation, integrating with:
- Arduino hardware for motor control via serial communication
- Assetto Corsa racing simulator for real-time physics data (pitch/roll monitoring)
- Potentiometer-based position detection for motor positioning

## Requirements

- Python 3.x
- Django 5.2.5
- pyserial for Arduino communication

## Setup

### Backend (Django)

1. **Activate virtual environment:**
   ```bash
   env\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database setup:**
   ```bash
   python manage.py migrate
   ```

4. **Run development server (with WebSocket support):**
   ```bash
   daphne -b 0.0.0.0 -p 9000 simulator.asgi:application
   ```

### Frontend (React + Vite)

1. **Navigate to frontend directory:**
   ```bash
   cd front
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment variables:**

   Copy the example environment file and update with your backend URL:
   ```bash
   cp .env.example .env
   ```

   Edit `front/.env` and set your Django backend server address:
   ```env
   VITE_API_BASE_URL=http://100.120.143.100:9000
   ```

   **Note:** Vite automatically loads `.env` files. Variables prefixed with `VITE_` are exposed to the client code. Restart the dev server after changing `.env` values.

4. **Run development server:**
   ```bash
   npm run dev
   ```

   Frontend runs on port 8080 by default.

## Management Commands

### arduino_control

Controls Arduino motor and monitors Assetto Corsa physics data.

**Usage:**
```bash
python manage.py arduino_control [options]
```

**Options:**
- `--port`: Specify serial port directly (e.g., COM3)
- `--baudrate`: Serial communication baud rate (default: 9600)

**Example:**
```bash
python manage.py arduino_control --port COM3 --baudrate 9600
```

**Current Functionality:**
- Connects to Assetto Corsa for real-time physics monitoring
- Monitors pitch and roll data continuously
- Arduino serial communication code available but currently commented out

## Architecture

- **simulator/** - Django project configuration
- **motion_control/** - Main app containing models, views, and hardware control logic
- **env/** - Python virtual environment
- **db.sqlite3** - SQLite development database

## Development Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations  
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Django shell
python manage.py shell
```

## Hardware Integration

The system is designed to work with:
- Arduino DC motor controllers
- MPU (Motion Processing Unit) sensors
- Potentiometer-based rotation detection
- Serial communication for motor control commands

## Potentiometer Calibration

Each motor has its own potentiometer that maps raw ADC readings (0–4095) to angles (0°–180°).
Because the motors are mounted mirrored, the pot travels in opposite directions.

> **IMPORTANT — Safety warnings:**
> - **Disconnect the physical arms/structure from the motors before calibrating.** During this process the motors move freely and uncontrolled movement with the structure attached can cause mechanical damage or injury.
> - **Repeat this calibration every time the potentiometer is repositioned or re-mounted.** If the potentiometer moves even slightly on its shaft, the angle mapping will be wrong and the system will not position correctly.

The calibration constants are defined in `arduino_esp32/dc_speed_direction_control/dc_speed_direction_control.ino`:

| Constant | Motor | Position |
|---|---|---|
| `POT_LEFT_0` | Left (0) | 0° |
| `POT_LEFT_180` | Left (0) | 180° |
| `POT_RIGHT_0` | Right (1) | 0° |
| `POT_RIGHT_180` | Right (1) | 180° |

> The raw ADC values for each constant depend on your specific hardware and potentiometer mounting. They must be measured on your setup — do not use values from another unit.

**How to recalibrate:**
1. **Disconnect the arms/structure** from both motors
2. Run the application and open the frontend
3. Use the **Forward** / **Backward** buttons on each motor card to jog the motor manually
4. Move the motor to the 0° physical position and read the **POT Value** shown in the motor card
5. Move the motor to the 180° physical position and read the **POT Value**
6. Update the four constants above in the `.ino` file with the measured values and re-flash

## DCS World Integration

To use the motion platform with DCS World:

1. **Configure Export.lua** - Create the file `%USERPROFILE%\Saved Games\DCS\Scripts\Export.lua` with the telemetry export code
2. **Restart DCS World** - Required for the Export.lua to take effect
3. **Run telemetry script** - Execute `python dcs_telemetry.py` to monitor pitch/roll data
4. **Start flying** - Telemetry only works when actively flying in a mission

For detailed setup instructions, see [doc/dcs_telemetry_setup.md](doc/dcs_telemetry_setup.md)