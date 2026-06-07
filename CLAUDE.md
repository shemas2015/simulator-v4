# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django-based motion control simulator integrating Arduino hardware control with multiple flight/racing simulator games. The system reads real-time physics data (via shared memory or telemetry files) and sends motor control commands to two ESP32-driven motors to simulate pitch and roll movement.

**Core Architecture:**
- Django 5.2.5 framework with single `motion_control` app
- Multi-game support: Assetto Corsa (shared memory) and DCS World (telemetry file)
- Arduino/ESP32 serial communication using `pyserial`
- Custom management command for orchestrating the entire system
- Standalone simulator for testing without games running
- WebSocket backend (`motion_control/consumers.py`) for real-time frontend communication

## Key Components

**motion_control/arduino_controller.py** - `ArduinoController` class handling serial communication, motor commands (speed/angle), connection management, and real-time target updates while motor is moving

**motion_control/games/assetto_corsa.py** - `AssettoPhysics` class reading Assetto Corsa shared memory, monitoring longitudinal G-forces (`accG[2]`), and triggering Arduino commands based on physics events

**motion_control/games/DCS_world.py** - `DcsWorldTelemetry` class reading DCS World telemetry file (`~/Saved Games/DCS/telemetry.txt`), calculating pitch/roll displacement using trigonometry, and sending angle commands to both motors. Configurable via `config` dict (including `motor_speed`, geometry parameters, input/output ranges)

**motion_control/consumers.py** - Django Channels WebSocket consumer for real-time communication between frontend and Arduino controllers

**motion_control/management/commands/arduino_control.py** - Main Django management command that initializes Arduino connections, starts game physics monitoring in background thread, and keeps system running

**sim_info.py** - Assetto Corsa shared memory interface using ctypes structures (`SPageFilePhysics`, `SPageFileGraphic`, `SPageFileStatic`)

**ac_simulator.py** - Standalone Assetto Corsa simulator writing fake physics data to shared memory for testing without game running

**arduino_esp32/dc_speed_direction_control/dc_speed_direction_control.ino** - ESP32 Arduino sketch for IBT-2 motor driver. Handles potentiometer feedback for angle control, per-motor calibration constants, forward/backward serial commands (`f`/`b`) for manual positioning, and `r` command to trigger `ESP.restart()`

**front/** - React + Vite + TypeScript frontend application for motor control interface with shadcn/ui components

## Key Frontend Components

**front/src/pages/Index.tsx** - Main dashboard page with dual motor configuration UI, start/stop listening controls, and connection status summary

**front/src/components/MotorCard.tsx** - Reusable motor card component managing individual motor connection state, position selection (left/right), test connection, potentiometer value display during calibration, and Forward/Backward buttons that send `f`/`b` commands to ESP32 for manual positioning

**front/src/App.tsx** - Root application component with React Router setup, TanStack Query for data fetching, toast notifications (Sonner), and tooltip provider

## Development Commands

**Environment:**
```bash
# Activate virtual environment (Windows)
env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Django:**
```bash
# Run development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Django shell
python manage.py shell

# Run tests
python manage.py test
```

**Arduino Motor Control (Main System):**
```bash
# Start Arduino control with Assetto Corsa monitoring
python manage.py arduino_control --port COM3 --baudrate 9600

# List available COM ports (run without --port)
python manage.py arduino_control
```

**Testing Without Assetto Corsa:**
```bash
# Terminal 1: Start AC simulator (writes to shared memory)
python ac_simulator.py

# Terminal 2: Run arduino_control command
python manage.py arduino_control --port COM3
```

**Frontend (React):**
```bash
# Navigate to frontend directory
cd front

# Install dependencies
npm install

# Start development server (runs on port 8080)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

## System Behavior

1. `arduino_control` command connects to two Arduino/ESP32 controllers via serial ports
2. Creates the appropriate game telemetry instance (`AssettoPhysics` or `DcsWorldTelemetry`) with both motor references
3. Spawns background thread monitoring physics/telemetry data
4. Main thread runs infinite loop keeping system alive
5. Telemetry thread reads data continuously and sends `speed,angle` commands to each motor based on calculated pitch/roll
6. Frontend communicates with backend via WebSocket (`/ws/arduino/`)
7. Logs to both console and `logs/arduino_control.log`

## Hardware Integration

**Arduino/ESP32 Setup:**
- IBT-2 motor driver with ESP32
- Pin configuration: RPWM=25, LPWM=26, R_EN=27, L_EN=14; potentiometer on pin 34
- Serial communication at 9600 baud
- Command format: `speed,angle\n` where speed=0-255, angle=0-180
- Manual commands: `f` (forward), `b` (backward) for calibration positioning
- Reset command: `r` triggers `ESP.restart()` to re-enter motor selection setup
- Per-motor potentiometer calibration constants: `POT_LEFT_0/180` and `POT_RIGHT_0/180`

**Assetto Corsa Integration:**
- Reads physics via Windows shared memory names: `acpmf_physics`, `acpmf_graphics`, `acpmf_static`
- Monitors longitudinal acceleration (`physics.accG[2]`)
- Physics structure includes pitch, roll, gear, speed, RPM, G-forces, etc.

**DCS World Integration:**
- Reads telemetry from `~/Saved Games/DCS/telemetry.txt`
- Calculates left/right motor displacement from pitch and roll using platform geometry
- Configurable parameters: motor positions, displacement ranges, scale factor, `motor_speed` (default 160)

## Frontend Architecture

**Tech Stack:**
- React 18.3 with TypeScript
- Vite 5.4 for build tooling and dev server
- TailwindCSS 3.4 for styling
- shadcn/ui component library (Radix UI primitives)
- TanStack Query for data fetching/state management
- React Router v6 for routing
- Sonner for toast notifications
- Lucide React for icons

**UI Features:**
- Dual motor configuration interface with position selection (left/right motor)
- Real-time connection status monitoring with visual indicators
- Test connection functionality with loading states
- Start/stop listening controls with validation
- Connection summary dashboard showing total motors, configured count, and active sessions
- Forward/Backward buttons for manual motor positioning during calibration
- Potentiometer (POT) value display in real time during calibration mode
- ESP32 restart flow triggered from frontend via Forward/Backward buttons on page load
- WebSocket-based communication with Django backend
- Responsive design with card-based layout
- Dark mode support via next-themes
- ESP32 restart sent automatically via `beforeunload` when listening is active

## Important Notes

- Arduino controller waits 2 seconds after connection for Arduino reset
- Direction changes require motor stop + 50ms delay to prevent hardware damage
- Logging configured to write verbose logs to `logs/arduino_control.log`
- System uses background threading - main thread must stay alive for monitoring to continue
- Shared memory only works on Windows (Assetto Corsa requirement)
- DCS World telemetry file path is configurable in `DcsWorldTelemetry.config['telemetry_file']`
- Frontend runs on port 8080, Django backend on port 9000 (configured via `VITE_API_BASE_URL`)
- WebSocket URL is derived from `VITE_API_BASE_URL` by replacing `http` with `ws`
- Motor speed for DCS World is configurable via `config['motor_speed']` (default: 160, range: 0-255)