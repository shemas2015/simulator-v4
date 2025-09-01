# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django-based motion control simulator project with hardware integration. The project appears to be in early development stages with a fresh Django setup.

**Architecture:**
- Django 5.2.5 web framework
- Single `motion_control` Django app for handling motion control logic
- SQLite database for development
- Python virtual environment in `env/` directory

**Key Components:**
- `simulator/` - Django project configuration and settings
- `motion_control/` - Django app containing models, views, and motion control logic
- `manage.py` - Django management script
- `requirements.txt` - Contains only Django dependency currently

## Development Commands

**Environment Setup:**
```bash
# Activate virtual environment (Windows)
env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Django Development:**
```bash
# Run development server
python manage.py runserver

# Create and apply database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin
python manage.py createsuperuser

# Start Django shell
python manage.py shell

# Run tests
python manage.py test
```

**Database Management:**
```bash
# Reset database (SQLite)
del db.sqlite3
python manage.py migrate
```

## Development Notes

- The project uses SQLite for development (db.sqlite3)
- `motion_control` app is created but not yet added to INSTALLED_APPS in settings
- Virtual environment is included in the repository (consider adding to .gitignore)
- Standard Django project structure with minimal customization
- Git history shows this is related to Arduino DC motor control with MPU sensors and potentiometer-based rotation detection

## Context from Git History

Based on recent commits, this simulator is related to:
- Arduino DC motor controller with MPU (motion processing unit)
- Potentiometer-based position detection (moved from MPU to potentiometer method)
- Motor direction safety and positioning logic
- Speed and angle control for motor movement (up/down positioning)

The Django project appears to be a web interface/simulator for the physical Arduino motor control system.