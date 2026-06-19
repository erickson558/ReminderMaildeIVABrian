"""
email_sender.py — Lógica de envío de correos electrónicos.

Soporta dos métodos:
  1. Outlook COM automation  → cuentas Exchange / Office 365 empresarial
  2. SMTP directo (STARTTLS) → cuentas personales (Hotmail, Gmail, etc.)

La función replace_placeholders() transforma variables de fecha en el cuerpo.
"""

import datetime
import logging
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

logger = logging.getLogger(__name__)

# ── Meses en español para reemplazo de placeholder ────────────────────────────
_MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


class EmailSendError(Exception):
    """Excepción personalizada que agrupa todos los fallos de envío de correo."""
    pass


def replace_placeholders(body: str) -> str:
    """
    Sustituye marcadores de fecha en el cuerpo del correo:
      [Mes en letras]  → nombre del mes actual en español  (ej. "Junio")
      [año en numero]  → año actual con 4 dígitos          (ej. "2026")
    """
    now = datetime.datetime.now()
    body = body.replace("[Mes en letras]", _MESES_ES[now.month])
    body = body.replace("[año en numero]", str(now.year))
    return body


# ── Método 1: Outlook COM ──────────────────────────────────────────────────────

def send_via_outlook_com(
    recipients: List[str],
    subject: str,
    body: str,
    account_smtp: str,
) -> None:
    """
    Envía un correo a través de la automatización COM de Microsoft Outlook.
    Recomendado para cuentas Exchange / Office 365 empresarial.

    Args:
        recipients:    Lista de correos destinatarios.
        subject:       Asunto del correo.
        body:          Cuerpo en texto plano.
        account_smtp:  Dirección SMTP de la cuenta remitente configurada en Outlook.

    Raises:
        EmailSendError: Si pywin32 no está instalado, la cuenta no se encuentra,
                        o Outlook devuelve cualquier error.
    """
    # Verificar que pywin32 esté disponible antes de intentar conectar
    try:
        import win32com.client as win32
    except ImportError:
        raise EmailSendError(
            "pywin32 no está instalado. Ejecuta: pip install pywin32"
        )

    try:
        outlook = win32.Dispatch("Outlook.Application")

        # Crear un nuevo elemento de correo (0 = olMailItem)
        mail = outlook.CreateItem(0)
        mail.Subject = subject
        mail.Body = body

        # Buscar la cuenta remitente en la lista de cuentas de Outlook
        account_found = False
        for account in outlook.Session.Accounts:
            if account.SmtpAddress.lower() == account_smtp.lower():
                mail.SendUsingAccount = account  # Forzar cuenta de envío
                account_found = True
                break

        if not account_found:
            raise EmailSendError(
                f"La cuenta '{account_smtp}' no está configurada en Outlook.\n"
                "Agrégala en Archivo → Configuración de la cuenta."
            )

        # Excluir al remitente de los destinatarios para evitar auto-envío
        filtered = [r for r in recipients if r.lower() != account_smtp.lower()]
        if not filtered:
            raise EmailSendError(
                "No quedan destinatarios válidos después de filtrar la cuenta remitente."
            )

        mail.To = "; ".join(filtered)
        mail.Send()
        logger.info("Correo enviado via Outlook COM desde %s a %s", account_smtp, filtered)

    except EmailSendError:
        raise  # Re-lanzar sin envolver
    except Exception as exc:
        raise EmailSendError(f"Error en automatización COM de Outlook: {exc}") from exc


# ── Método 2: SMTP directo ─────────────────────────────────────────────────────

def send_via_smtp(
    from_email: str,
    recipients: List[str],
    subject: str,
    body: str,
    password: str,
    smtp_server: str,
    smtp_port: int = 587,
) -> None:
    """
    Envía un correo directamente por SMTP con STARTTLS.
    Necesario para cuentas personales (Hotmail, Gmail) que no funcionan bien
    con el método COM de Outlook.

    ¡IMPORTANTE para Hotmail/Outlook.com!
    No uses tu contraseña normal. Crea un "App Password":
      1. Ve a account.microsoft.com/security
      2. Activa la verificación en dos pasos
      3. Genera un App Password y úsalo aquí

    Args:
        from_email:  Correo remitente (tu dirección Hotmail/Gmail).
        recipients:  Lista de destinatarios.
        subject:     Asunto del correo.
        body:        Cuerpo en texto plano.
        password:    App Password (no tu contraseña normal de Windows).
        smtp_server: Servidor SMTP (ej. "smtp-mail.outlook.com").
        smtp_port:   Puerto SMTP (default 587 para STARTTLS).

    Raises:
        EmailSendError: Si la autenticación falla, no se puede conectar,
                        o los destinatarios son rechazados.
    """
    # Construir el mensaje MIME con codificación UTF-8
    msg = MIMEMultipart("alternative")
    msg["From"] = from_email
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = Header(subject, "utf-8").encode()
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        # Conectar al servidor SMTP y negociar cifrado STARTTLS
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.ehlo()           # Presentarse al servidor
            server.starttls()       # Iniciar cifrado TLS
            server.ehlo()           # Volver a presentarse tras TLS
            server.login(from_email, password)
            server.sendmail(from_email, recipients, msg.as_string())

        logger.info(
            "Correo enviado via SMTP (%s:%d) desde %s a %s",
            smtp_server, smtp_port, from_email, recipients,
        )

    except smtplib.SMTPAuthenticationError:
        raise EmailSendError(
            "Autenticación SMTP fallida.\n\n"
            "Para Hotmail / Outlook.com personal:\n"
            "  1. Activa verificación en 2 pasos en account.microsoft.com\n"
            "  2. Ve a Seguridad → Contraseñas de aplicación\n"
            "  3. Genera una contraseña y úsala en el campo 'Contraseña SMTP'\n\n"
            "Para Gmail:\n"
            "  1. Activa verificación en 2 pasos\n"
            "  2. Genera una Contraseña de aplicación en myaccount.google.com"
        )
    except smtplib.SMTPConnectError as exc:
        raise EmailSendError(
            f"No se pudo conectar a {smtp_server}:{smtp_port}.\n"
            f"Verifica tu conexión a Internet. Detalle: {exc}"
        ) from exc
    except smtplib.SMTPRecipientsRefused as exc:
        raise EmailSendError(f"El servidor rechazó uno o más destinatarios: {exc}") from exc
    except Exception as exc:
        raise EmailSendError(f"Error SMTP inesperado: {exc}") from exc
