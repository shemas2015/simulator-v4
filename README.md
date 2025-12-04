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

## DCS World Integration

To use the motion platform with DCS World:

1. **Configure Export.lua** - Create the file `%USERPROFILE%\Saved Games\DCS\Scripts\Export.lua` with the telemetry export code
2. **Restart DCS World** - Required for the Export.lua to take effect
3. **Run telemetry script** - Execute `python dcs_telemetry.py` to monitor pitch/roll data
4. **Start flying** - Telemetry only works when actively flying in a mission

For detailed setup instructions, see [doc/dcs_telemetry_setup.md](doc/dcs_telemetry_setup.md)