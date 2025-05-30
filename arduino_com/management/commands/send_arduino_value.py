import time
import serial
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Send direction and speed value to Arduino'

    def add_arguments(self, parser):
        parser.add_argument('--port', type=str, default='/dev/ttyUSB0', help='Serial port (default: /dev/ttyUSB0)')

    def handle(self, *args, **options):
        port = options['port']
        try:
            arduino = serial.Serial(port=port, baudrate=9600, timeout=.1)
        except serial.SerialException:
            raise CommandError(f"No se pudo abrir el puerto {port}")

        self.stdout.write(self.style.SUCCESS(f"Conectado a {port}. Presiona Ctrl+C para salir."))

        try:
            while True:
                # Leer dirección
                direction = input("Dirección (1 o 2, 'q' para salir): ").strip()
                if direction.lower() == 'q':
                    break
                if direction not in ['1', '2']:
                    print("⚠️ Dirección inválida. Debe ser 1 o 2.")
                    continue

                # Leer velocidad
                speed = input("Velocidad (1 a 99): ").strip()
                if not speed.isdigit():
                    print("⚠️ Velocidad inválida. Debe ser un número entre 1 y 99.")
                    continue
                speed = int(speed)
                if not (1 <= speed < 100):
                    print("⚠️ Velocidad fuera de rango.")
                    continue

                # Enviar datos al Arduino
                arduino.write(f"{direction}\n".encode('utf-8'))
                time.sleep(0.05)
                arduino.write(f"{speed}\n".encode('utf-8'))
                time.sleep(0.05)

                # Leer respuesta del Arduino
                data = arduino.readline()
                print(f"Arduino responde: {data.decode().strip()}")

        except KeyboardInterrupt:
            print("\nFinalizado por el usuario.")
