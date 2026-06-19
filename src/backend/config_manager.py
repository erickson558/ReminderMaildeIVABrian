"""
config_manager.py — Gestión de configuración de la aplicación.

Responsabilidad única: leer y escribir config.json.
El archivo de configuración vive junto al ejecutable (o al script raíz).
"""

import json
import logging
import os
import sys
from typing import Any, Dict

logger = logging.getLogger(__name__)

# ── Valores por defecto ────────────────────────────────────────────────────────
# Cualquier clave ausente en config.json se completará con estos valores.
DEFAULT_CONFIG: Dict[str, Any] = {
    "destinatarios": [],        # Lista de correos destinatarios
    "asunto": "",               # Asunto del correo
    "cuerpo": "",               # Cuerpo del correo (acepta [Mes en letras] y [año en numero])
    "auto_close": True,         # Cerrar la app automáticamente tras enviar
    "auto_close_delay": 60,     # Segundos de espera antes de cerrar
    "smtp_password": "",        # Contraseña / App Password para cuentas SMTP (Hotmail, Gmail)
    "language": "es",           # Idioma de la interfaz: "es" o "en"
    "selected_account": "",     # Última cuenta de envío seleccionada
}


def get_base_path() -> str:
    """
    Devuelve el directorio base de la aplicación.
    - Modo ejecutable (.exe): directorio del .exe
    - Modo script: directorio raíz del proyecto (3 niveles arriba de este archivo)
    """
    if getattr(sys, "frozen", False):
        # PyInstaller coloca sys.executable apuntando al .exe
        return os.path.dirname(sys.executable)
    # src/backend/config_manager.py → subir 3 niveles = raíz del proyecto
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def get_config_path() -> str:
    """Devuelve la ruta absoluta a config.json."""
    return os.path.join(get_base_path(), "config.json")


def load_config() -> Dict[str, Any]:
    """
    Carga la configuración desde config.json.
    Si el archivo no existe o tiene errores, devuelve los valores por defecto.
    Las claves nuevas (no presentes en el JSON guardado) se rellenan con DEFAULT_CONFIG.
    """
    # Partir de los valores por defecto para garantizar que todas las claves existen
    config: Dict[str, Any] = dict(DEFAULT_CONFIG)
    config_path = get_config_path()

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # Sobrescribir sólo las claves presentes en el archivo guardado
            config.update(loaded)
            logger.debug("Configuración cargada desde %s", config_path)
        except (json.JSONDecodeError, IOError) as exc:
            logger.error("No se pudo cargar config.json: %s", exc)
    else:
        logger.info("config.json no encontrado; usando valores por defecto")

    return config


def save_config(config: Dict[str, Any]) -> None:
    """
    Guarda el diccionario de configuración en config.json con formato indentado.
    Lanza IOError si no se puede escribir el archivo.
    """
    config_path = get_config_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info("Configuración guardada en %s", config_path)
    except IOError as exc:
        logger.error("No se pudo guardar config.json: %s", exc)
        raise
