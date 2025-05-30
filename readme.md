# car_simulator - Arduino Serial Communication via Django

## 1. Download from Git

Clone the repository to your local machine:

```bash
git clone https://github.com/yourusername/car_simulator.git
cd car_simulator
```

## 2. Install dependencies

Make sure you have Python 3.12 installed.

Then install required packages:

```bash
pip install -r requirements.txt
```

## 3. Python Version

This project requires **Python 3.12** or higher.

Check your Python version with:

```bash
python --version
```

## 4. Run the serial command

Send a value between 1 and 99 to the Arduino via serial with this command:

```bash
python manage.py send_arduino_value <value> [--port <serial_port>]
```

- `<value>`: integer between 1 and 99 (required)
- `--port <serial_port>`: optional, default is `/dev/ttyUSB0` (use the correct port for your system)

**Example:**

```bash
python manage.py send_arduino_value 45 --port /dev/ttyUSB0
```

---

If you have any questions, please open an issue or contact the maintainer.