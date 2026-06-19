"""
account_manager.py — Descubrimiento y clasificación de cuentas de correo.

Responsabilidades:
  - Consultar las cuentas configuradas en Microsoft Outlook (via COM).
  - Detectar si una dirección pertenece a un dominio personal (Hotmail, Gmail…).
  - Proveer la configuración SMTP correcta para cada dominio.
"""

import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Dominios que requieren SMTP directo ───────────────────────────────────────
# Outlook COM (SendUsingAccount) no es confiable para cuentas personales de
# Microsoft porque usa autenticación moderna incompatible con la automatización
# de COM en muchos escenarios.
PERSONAL_DOMAINS = frozenset({
    "hotmail.com", "hotmail.es", "hotmail.co.uk",
    "outlook.com", "outlook.es",
    "live.com", "live.com.mx",
    "msn.com",
    "gmail.com",
    "yahoo.com", "yahoo.es",
})

# ── Servidores SMTP por dominio ───────────────────────────────────────────────
# (servidor, puerto TLS/STARTTLS)
SMTP_CONFIG: dict = {
    "hotmail.com":    ("smtp-mail.outlook.com", 587),
    "hotmail.es":     ("smtp-mail.outlook.com", 587),
    "hotmail.co.uk":  ("smtp-mail.outlook.com", 587),
    "outlook.com":    ("smtp-mail.outlook.com", 587),
    "outlook.es":     ("smtp-mail.outlook.com", 587),
    "live.com":       ("smtp-mail.outlook.com", 587),
    "live.com.mx":    ("smtp-mail.outlook.com", 587),
    "msn.com":        ("smtp-mail.outlook.com", 587),
    "gmail.com":      ("smtp.gmail.com", 587),
    "yahoo.com":      ("smtp.mail.yahoo.com", 587),
    "yahoo.es":       ("smtp.mail.yahoo.com", 587),
}


def get_outlook_accounts() -> List[str]:
    """
    Retorna las direcciones SMTP de todas las cuentas configuradas en Outlook.
    Devuelve lista vacía si Outlook no está disponible o falla.
    """
    try:
        import win32com.client as win32  # pywin32 — sólo disponible en Windows
        outlook = win32.Dispatch("Outlook.Application")
        accounts = outlook.Session.Accounts
        result = [acc.SmtpAddress for acc in accounts if acc.SmtpAddress]
        logger.debug("Cuentas Outlook encontradas: %s", result)
        return result
    except Exception as exc:
        logger.warning("No se pudieron obtener cuentas de Outlook: %s", exc)
        return []


def is_personal_account(email: str) -> bool:
    """
    Devuelve True si el correo pertenece a un dominio personal que requiere SMTP.
    Ejemplo: hotmail.com, gmail.com, outlook.com personal.
    """
    if "@" not in email:
        return False
    domain = email.split("@")[-1].lower()
    return domain in PERSONAL_DOMAINS


def get_smtp_config(email: str) -> Optional[Tuple[str, int]]:
    """
    Retorna (servidor_smtp, puerto) para el dominio del correo dado.
    Devuelve None si el dominio no está en el mapa SMTP_CONFIG.
    """
    if "@" not in email:
        return None
    domain = email.split("@")[-1].lower()
    return SMTP_CONFIG.get(domain)
