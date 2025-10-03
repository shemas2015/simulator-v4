# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django-based motion control simulator integrating Arduino hardware control with Assetto Corsa racing simulator physics monitoring. The system reads real-time physics data from Assetto Corsa via shared memory and sends motor control commands to Arduino via serial communication.

**Core Architecture:**
- Django 5.2.5 framework with single `motion_control` app
- Assetto Corsa physics monitoring via Windows shared memory (`mmap`)
- Arduino serial communication using `pyserial`
- Custom management command for orchestrating the entire system
- Standalone simulator for testing without Assetto Corsa running

## Key Components

**motion_control/arduino_controller.py** - `ArduinoController` class handling serial communication, motor commands (speed/angle), connection management, and interactive control mode

**motion_control/assetto_physics.py** - `AssettoPhysics` class reading Assetto Corsa shared memory, monitoring longitudinal G-forces (`accG[2]`), and triggering Arduino commands based on physics events

**motion_control/management/commands/arduino_control.py** - Main Django management command that initializes Arduino connection, starts physics monitoring in background thread, and keeps system running

**sim_info.py** - Assetto Corsa shared memory interface using ctypes structures (`SPageFilePhysics`, `SPageFileGraphic`, `SPageFileStatic`)

**ac_simulator.py** - Standalone Assetto Corsa simulator writing fake physics data to shared memory for testing without game running

**motor_reverse/motor_reverse.ino** - Arduino sketch for IBT-2 motor driver using ESP32 pins, handles forward/backward motor control with safety pauses

**front/** - React + Vite + TypeScript frontend application for motor control interface with shadcn/ui components

## Key Frontend Components

**front/src/pages/Index.tsx** - Main dashboard page with dual motor configuration UI, start/stop listening controls, and connection status summary

**front/src/components/MotorCard.tsx** - Reusable motor card component managing individual motor connection state, position selection (left/right), and test connection functionality

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

1. `arduino_control` command connects to Arduino via serial port
2. Creates `AssettoPhysics` instance with Arduino controller reference
3. Spawns background thread monitoring physics data (currently: longitudinal G-force `accG[2]`)
4. Main thread runs infinite loop keeping system alive
5. Physics monitoring thread reads shared memory continuously and sends commands to Arduino based on events
6. Initial command sends speed=100, angle=90 to Arduino on startup
7. Logs to both console and `logs/arduino_control.log`

## Hardware Integration

**Arduino Setup:**
- IBT-2 motor driver with ESP32
- Pin configuration: RPWM=25, LPWM=26, R_EN=27, L_EN=14
- Serial communication at 9600 baud
- Command format: `speed,angle\n` where speed=0-255, angle=0-180

**Assetto Corsa Integration:**
- Reads physics via Windows shared memory names: `acpmf_physics`, `acpmf_graphics`, `acpmf_static`
- Currently monitors longitudinal acceleration (`physics.accG[2]`)
- Physics structure includes pitch, roll, gear, speed, RPM, G-forces, etc.

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
- Responsive design with card-based layout
- Dark mode support via next-themes

**Current Limitations:**
- Frontend UI is currently mockup-only with simulated connection testing (2-second delay)
- No backend integration yet - motor connection, position changes, and listening state are client-side only
- Backend API endpoints need to be created in Django to handle motor control and physics monitoring

## Important Notes

- Arduino controller waits 2 seconds after connection for Arduino reset
- Direction changes require motor stop + 50ms delay to prevent hardware damage
- Logging configured to write verbose logs to `logs/arduino_control.log`
- System uses background threading - main thread must stay alive for monitoring to continue
- Shared memory only works on Windows (Assetto Corsa requirement)
- Frontend runs on port 8080, Django backend on default port 8000