"""
translations.py — Motor de internacionalización (i18n).

Carga traducciones desde archivos JSON por idioma y expone la función t()
para obtener texto traducido en cualquier parte de la aplicación.

Uso:
    from src.i18n.translations import load_language, t
    load_language("es")
    print(t("send"))          # → "Enviar"
    load_language("en")
    print(t("send"))          # → "Send"
    print(t("hi", name="X"))  # → "Hello X"  (si la cadena tiene {name})
"""

import json
import logging
import os
import sys
from typing import Dict

logger = logging.getLogger(__name__)

# ── Constantes ─────────────────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = ("es", "en")
DEFAULT_LANGUAGE = "es"

# Caché en memoria: { "es": {"send": "Enviar", ...}, "en": {...} }
_cache: Dict[str, Dict[str, str]] = {}
_current_lang = DEFAULT_LANGUAGE


def _translations_dir() -> str:
    """
    Devuelve el directorio que contiene los archivos JSON de traducción.
    - Modo ejecutable (.exe): PyInstaller extrae los datos en sys._MEIPASS
    - Modo script: el mismo directorio donde vive este archivo
    """
    if getattr(sys, "frozen", False):
        # PyInstaller extrae los datas aquí en tiempo de ejecución
        return os.path.join(getattr(sys, "_MEIPASS", ""), "src", "i18n")
    return os.path.dirname(os.path.abspath(__file__))


def load_language(lang: str) -> None:
    """
    Carga el archivo de traducción para el idioma especificado.
    Si el idioma no está soportado o el archivo no existe, cae de vuelta a español.

    Args:
        lang: Código de idioma de dos letras ("es" o "en").
    """
    global _current_lang

    # Normalizar a minúsculas y validar soporte
    lang = lang.lower()
    if lang not in SUPPORTED_LANGUAGES:
        logger.warning("Idioma '%s' no soportado, usando '%s'", lang, DEFAULT_LANGUAGE)
        lang = DEFAULT_LANGUAGE

    # Cargar sólo si no está ya en caché
    if lang not in _cache:
        lang_file = os.path.join(_translations_dir(), f"{lang}.json")
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                _cache[lang] = json.load(f)
            logger.debug("Traducciones cargadas para idioma '%s'", lang)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            logger.error("No se pudo cargar %s: %s", lang_file, exc)
            _cache[lang] = {}

    _current_lang = lang


def t(key: str, **kwargs: str) -> str:
    """
    Traduce una clave al idioma activo.
    Soporta interpolación de formato: t("hola", name="Mundo") → "Hola Mundo".
    Si la clave no existe devuelve la propia clave como texto de respaldo.

    Args:
        key:    Clave de traducción (ej. "send", "email_sent").
        kwargs: Pares clave=valor para interpolación de texto.

    Returns:
        Texto traducido con interpolación aplicada.
    """
    lang_dict = _cache.get(_current_lang, {})
    text = lang_dict.get(key, key)  # Fallback: la propia clave si no existe

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError) as exc:
            logger.warning("Error de interpolación en clave '%s': %s", key, exc)

    return text


def get_current_language() -> str:
    """Devuelve el código del idioma activo ("es" o "en")."""
    return _current_lang


# Cargar idioma por defecto al importar el módulo
load_language(DEFAULT_LANGUAGE)
