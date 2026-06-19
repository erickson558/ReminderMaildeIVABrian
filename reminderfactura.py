"""
reminderfactura.py — Punto de entrada del Reminder IVA Brian.

Este archivo es intencionalmente delgado: sólo configura el logging
y lanza la GUI. Toda la lógica vive en src/.

Para compilar a .exe:
    pyinstaller reminderfactura.spec
"""

import logging
import os
import sys

# ── Directorio base (funciona tanto para .py como para .exe compilado) ─────────
_BASE = (
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)

# ── Logging: archivo + consola ─────────────────────────────────────────────────
# El archivo de log se crea en el mismo directorio que el .exe o el script.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(
            os.path.join(_BASE, "reminder.log"), encoding="utf-8"
        ),
        logging.StreamHandler(sys.stdout),
    ],
)

# ── Lanzar aplicación ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    from src.frontend.app import ReminderApp

    app = ReminderApp()
    app.run()
