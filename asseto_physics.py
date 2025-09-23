# read_ac_physics.py
# Requisitos: sim_info.py y _ctypes.pyd accesibles en PYTHONPATH
from sim_info import info
import time
import os

def dump_physics_once():
    phys = info.physics
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

def main(poll_hz=10):
    interval = 1.0 / poll_hz
    print("Esperando Assetto Corsa... (Ctrl+C para salir)")
    try:
        while True:
            os.system("cls" if os.name == "nt" else "clear")
            print(time.strftime("%Y-%m-%d %H:%M:%S"))
            dump_physics_once()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nDetenido por usuario.")

if __name__ == "__main__":
    main(poll_hz=10)  # cambia poll_hz si quieres más/menos frecuencia
