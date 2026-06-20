"""
app.py — Interfaz gráfica principal (Tkinter) del Reminder IVA Brian.

Patrón:
  - Este módulo sólo maneja la GUI.
  - Toda la lógica de negocio (envío, configuración, cuentas) vive en src/backend/.
  - Los textos de la UI se obtienen de src/i18n/ para soporte multi-idioma.

Flujo de envío:
  1. Usuario pulsa "Enviar".
  2. Se validan destinatarios y cuenta.
  3. El envío corre en un hilo secundario (no congela la ventana).
  4. El resultado actualiza la barra de estado en el hilo principal.
  5. Si auto-cierre está activo, se programa root.after() para destruir la ventana.
"""

import logging
import threading
import tkinter as tk
import webbrowser
from tkinter import simpledialog, ttk

# ── Módulos internos ───────────────────────────────────────────────────────────
from src.backend.account_manager import (
    get_outlook_accounts,
    get_smtp_config,
    is_personal_account,
)
from src.backend.config_manager import load_config, save_config
from src.backend.email_sender import (
    EmailSendError,
    replace_placeholders,
    send_via_outlook_com,
    send_via_smtp,
)
from src.i18n.translations import get_current_language, load_language, t

logger = logging.getLogger(__name__)

# ── Constantes ─────────────────────────────────────────────────────────────────
DONATE_URL = "https://www.paypal.com/donate/?hosted_button_id=ZABFRXC2P3JQN"
WINDOW_MIN_W = 520
WINDOW_MIN_H = 650


def _normalize_recipients(emails) -> list[str]:
    """Limpia espacios y elimina destinatarios vacíos o duplicados."""
    normalized = []
    seen = set()
    for raw_email in emails:
        email = str(raw_email).strip()
        if not email:
            continue

        email_key = email.lower()
        if email_key in seen:
            continue

        seen.add(email_key)
        normalized.append(email)

    return normalized


class ReminderApp:
    """
    Clase principal de la aplicación.
    Encapsula la ventana Tkinter, todos los widgets y la coordinación
    entre la UI y los módulos backend.
    """

    def __init__(self) -> None:
        """
        Constructor: carga configuración, inicializa i18n y construye la ventana.
        """
        # Cargar configuración persistida (config.json)
        self.config = load_config()

        # Inicializar idioma guardado antes de crear cualquier texto de UI
        load_language(self.config.get("language", "es"))

        # Crear ventana principal de Tkinter
        self.root = tk.Tk()
        self.root.title(t("app_title"))
        self.root.minsize(WINDOW_MIN_W, WINDOW_MIN_H)
        self.root.resizable(True, True)

        # Variable interna para saber si hay un envío en curso
        # (evita doble-click en el botón Enviar)
        self._sending = False

        # Construir todos los widgets
        self._build_ui()

        # Poblar el combobox de cuentas Outlook (puede tardar si Outlook no está listo)
        self._refresh_accounts()

    # ── Construcción de la UI ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """
        Crea y organiza todos los widgets de la ventana.
        Se puede llamar de nuevo para reconstruir (ej. al cambiar idioma).
        """
        # ── Barra superior: selector de idioma + botón donación ───────────────
        bar = tk.Frame(self.root)
        bar.pack(fill=tk.X, padx=10, pady=(6, 0))

        tk.Label(bar, text=t("language_label")).pack(side=tk.LEFT)

        self.lang_var = tk.StringVar(value=self.config.get("language", "es"))
        lang_combo = ttk.Combobox(
            bar,
            textvariable=self.lang_var,
            values=list(("es", "en")),
            state="readonly",
            width=5,
        )
        lang_combo.pack(side=tk.LEFT, padx=(3, 0))
        # Reconstruir la UI cuando el usuario cambia el idioma
        lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)

        # Botón "Cómprame una cerveza" — enlaza a PayPal
        tk.Button(
            bar,
            text=t("btn_donate"),
            bg="#003087",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=6,
            command=self._open_donate,
        ).pack(side=tk.RIGHT)

        # ── Sección de destinatarios ───────────────────────────────────────────
        frm_dest = tk.LabelFrame(self.root, text=t("recipients_label"))
        frm_dest.pack(fill=tk.X, padx=10, pady=5)

        # Listbox con scrollbar vertical
        list_wrap = tk.Frame(frm_dest)
        list_wrap.pack(fill=tk.X, padx=5, pady=(4, 0))

        sb_dest = tk.Scrollbar(list_wrap, orient=tk.VERTICAL)
        self.listbox_dest = tk.Listbox(
            list_wrap,
            height=5,
            selectmode=tk.EXTENDED,  # Permite selección múltiple
            yscrollcommand=sb_dest.set,
        )
        sb_dest.config(command=self.listbox_dest.yview)
        self.listbox_dest.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_dest.pack(side=tk.RIGHT, fill=tk.Y)

        # Rellenar desde la configuración cargada
        for email in self.config.get("destinatarios", []):
            self.listbox_dest.insert(tk.END, email)

        # Botones Agregar / Eliminar
        btn_row = tk.Frame(frm_dest)
        btn_row.pack(pady=(4, 6))
        tk.Button(btn_row, text=t("add"),    width=14, command=self._add_recipient   ).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_row, text=t("remove"), width=14, command=self._remove_recipient).pack(side=tk.LEFT, padx=5)

        # ── Campo Asunto ───────────────────────────────────────────────────────
        tk.Label(self.root, text=t("subject_label"), anchor="w").pack(
            fill=tk.X, padx=12, pady=(4, 0)
        )
        self.entry_subject = tk.Entry(self.root)
        self.entry_subject.insert(0, self.config.get("asunto", ""))
        self.entry_subject.pack(fill=tk.X, padx=10, pady=(0, 4))

        # ── Campo Cuerpo ───────────────────────────────────────────────────────
        tk.Label(self.root, text=t("body_label"), anchor="w").pack(
            fill=tk.X, padx=12
        )
        body_wrap = tk.Frame(self.root)
        body_wrap.pack(fill=tk.BOTH, expand=True, padx=10)

        sb_body = tk.Scrollbar(body_wrap, orient=tk.VERTICAL)
        self.text_body = tk.Text(
            body_wrap,
            height=8,
            wrap=tk.WORD,
            yscrollcommand=sb_body.set,
        )
        sb_body.config(command=self.text_body.yview)
        self.text_body.insert("1.0", self.config.get("cuerpo", ""))
        self.text_body.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_body.pack(side=tk.RIGHT, fill=tk.Y)

        # ── Cuenta de envío ────────────────────────────────────────────────────
        frm_account = tk.LabelFrame(self.root, text=t("account_frame"))
        frm_account.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frm_account, text=t("account_label")).pack(
            anchor="w", padx=10, pady=(4, 0)
        )

        self.account_var = tk.StringVar()
        self.combo_account = ttk.Combobox(
            frm_account,
            textvariable=self.account_var,
            state="readonly",
            width=46,
        )
        self.combo_account.pack(anchor="w", padx=10, pady=(2, 6))
        # Detectar si la cuenta seleccionada necesita SMTP
        self.combo_account.bind("<<ComboboxSelected>>", self._on_account_change)

        # Etiqueta de aviso para cuentas personales (oculta por defecto)
        self.lbl_hotmail_hint = tk.Label(
            frm_account,
            text=t("hotmail_hint"),
            fg="#c75000",
            wraplength=450,
            justify=tk.LEFT,
            font=("TkDefaultFont", 8),
        )
        # No la empaquetamos todavía; _on_account_change la muestra/oculta

        # ── Contraseña SMTP (siempre visible — el usuario la ignora si no la necesita) ──
        frm_smtp = tk.LabelFrame(self.root, text=t("smtp_frame"))
        frm_smtp.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frm_smtp, text=t("smtp_label")).pack(anchor="w", padx=10, pady=(4, 0))

        self.smtp_pwd_var = tk.StringVar(value=self.config.get("smtp_password", ""))
        tk.Entry(frm_smtp, textvariable=self.smtp_pwd_var, show="*", width=42).pack(
            anchor="w", padx=10, pady=(2, 0)
        )
        # Texto de ayuda en gris debajo del campo
        tk.Label(
            frm_smtp,
            text=t("smtp_hint"),
            fg="gray",
            font=("TkDefaultFont", 8),
            wraplength=460,
            justify=tk.LEFT,
        ).pack(anchor="w", padx=10, pady=(2, 6))

        # ── Cierre automático ──────────────────────────────────────────────────
        frm_auto = tk.LabelFrame(self.root, text=t("auto_close_frame"))
        frm_auto.pack(fill=tk.X, padx=10, pady=5)

        self.auto_close_var = tk.BooleanVar(value=self.config.get("auto_close", True))
        tk.Checkbutton(
            frm_auto,
            text=t("auto_close_check"),
            variable=self.auto_close_var,
        ).pack(anchor="w", padx=10, pady=(4, 0))

        tk.Label(frm_auto, text=t("auto_close_delay_label")).pack(
            anchor="w", padx=10
        )
        self.auto_delay_var = tk.StringVar(
            value=str(self.config.get("auto_close_delay", 60))
        )
        tk.Entry(frm_auto, textvariable=self.auto_delay_var, width=8).pack(
            anchor="w", padx=10, pady=(0, 6)
        )

        # ── Botones de acción ──────────────────────────────────────────────────
        btn_row2 = tk.Frame(self.root)
        btn_row2.pack(pady=8)

        self.btn_send = tk.Button(
            btn_row2,
            text=t("btn_send"),
            width=17,
            bg="#0078d4",
            fg="white",
            command=self._send_email,
        )
        self.btn_send.pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_row2, text=t("btn_save"), width=17, command=self._save_config
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_row2, text=t("btn_exit"), width=17, command=self.root.destroy
        ).pack(side=tk.LEFT, padx=5)

        # ── Barra de estado ────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="")
        self.status_lbl = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padx=4,
        )
        self.status_lbl.pack(side=tk.BOTTOM, fill=tk.X)

    # ── Helpers de UI ──────────────────────────────────────────────────────────

    def _set_status(self, message: str, color: str = "black") -> None:
        """Actualiza la barra de estado con mensaje y color (ej. 'green', 'red')."""
        self.status_var.set(message)
        self.status_lbl.config(fg=color)
        logger.info("Status: %s", message)

    def _get_current_recipients(self) -> list[str]:
        """Devuelve la lista actual de destinatarios visible en la GUI."""
        return _normalize_recipients(self.listbox_dest.get(0, tk.END))

    def _get_delay_secs(self) -> int:
        """Parsea el campo de delay; devuelve 60 si el valor no es numérico."""
        try:
            return max(1, int(self.auto_delay_var.get()))
        except ValueError:
            return 60

    def _refresh_accounts(self) -> None:
        """
        Carga las cuentas de Outlook en el combobox.
        Restaura la última cuenta seleccionada si sigue disponible.
        """
        accounts = get_outlook_accounts()
        self.combo_account["values"] = accounts

        if accounts:
            saved = self.config.get("selected_account", "")
            if saved in accounts:
                self.combo_account.set(saved)
            else:
                self.combo_account.current(0)
            self._set_status(t("status_accounts_loaded"), "gray")
        else:
            self._set_status(t("status_no_outlook"), "orange")

        # Actualizar aviso de Hotmail según cuenta seleccionada
        self._on_account_change()

    def _on_account_change(self, _event=None) -> None:
        """
        Muestra u oculta el aviso de cuenta personal según la cuenta seleccionada.
        El campo SMTP siempre está visible; este aviso es sólo informativo.
        """
        selected = self.account_var.get()
        if is_personal_account(selected):
            # Mostrar etiqueta de aviso debajo del combobox
            self.lbl_hotmail_hint.pack(anchor="w", padx=10, pady=(0, 6))
        else:
            self.lbl_hotmail_hint.pack_forget()

    def _on_language_change(self, _event=None) -> None:
        """
        Cambia el idioma de la UI sin perder los datos introducidos por el usuario.
        Reconstruye todos los widgets con los nuevos textos.
        """
        new_lang = self.lang_var.get()
        load_language(new_lang)

        # Capturar estado actual de la UI antes de destruir los widgets
        self.config["language"] = new_lang
        self.config["destinatarios"]    = list(self.listbox_dest.get(0, tk.END))
        self.config["asunto"]           = self.entry_subject.get().strip()
        self.config["cuerpo"]           = self.text_body.get("1.0", tk.END).strip()
        self.config["smtp_password"]    = self.smtp_pwd_var.get()
        self.config["selected_account"] = self.account_var.get()
        self.config["auto_close"]       = self.auto_close_var.get()
        self.config["auto_close_delay"] = self._get_delay_secs()

        # Destruir todos los widgets y reconstruir con el nuevo idioma
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title(t("app_title"))
        self._build_ui()
        self._refresh_accounts()

    def _open_donate(self) -> None:
        """Abre el enlace de donación PayPal en el navegador predeterminado."""
        webbrowser.open(DONATE_URL)

    # ── Gestión de destinatarios ───────────────────────────────────────────────

    def _add_recipient(self) -> None:
        """Muestra un diálogo para ingresar un correo y lo agrega a la lista."""
        email = simpledialog.askstring(
            t("add_dialog_title"), t("add_dialog_prompt"), parent=self.root
        )
        if email and email.strip():
            self.listbox_dest.insert(tk.END, email.strip())
            self.config["destinatarios"] = self._get_current_recipients()
            self._set_status(t("status_recipient_added"), "green")

    def _remove_recipient(self) -> None:
        """Elimina los destinatarios seleccionados (soporta selección múltiple)."""
        selection = self.listbox_dest.curselection()
        if not selection:
            self._set_status(t("status_select_to_remove"), "red")
            return
        # Eliminar en orden inverso para no alterar los índices al borrar
        for idx in reversed(selection):
            self.listbox_dest.delete(idx)
        self.config["destinatarios"] = self._get_current_recipients()
        self._set_status(t("status_recipient_removed"), "green")

    # ── Guardar configuración ──────────────────────────────────────────────────

    def _save_config(self) -> None:
        """Persiste el estado actual de la UI en config.json."""
        config = {
            "destinatarios":    self._get_current_recipients(),
            "asunto":           self.entry_subject.get().strip(),
            "cuerpo":           self.text_body.get("1.0", tk.END).strip(),
            "auto_close":       self.auto_close_var.get(),
            "auto_close_delay": self._get_delay_secs(),
            "smtp_password":    self.smtp_pwd_var.get(),
            "language":         get_current_language(),
            "selected_account": self.account_var.get(),
        }
        try:
            save_config(config)
            self.config = config
            self._set_status(t("status_config_saved"), "green")
        except Exception as exc:
            self._set_status(t("status_config_error", error=str(exc)), "red")

    # ── Envío de correo ────────────────────────────────────────────────────────

    def _send_email(self) -> None:
        """
        Inicia el envío de correo en un hilo secundario.
        La GUI permanece responsiva durante el envío.
        Deshabilita el botón Enviar para evitar doble-click.
        """
        # Evitar envíos simultáneos
        if self._sending:
            return

        # Recopilar y validar datos de la UI antes de lanzar el hilo
        recipients = self._get_current_recipients()
        if not recipients:
            self._set_status(t("status_no_recipients"), "red")
            return

        selected_account = self.account_var.get().strip()
        if not selected_account:
            self._set_status(t("status_no_account"), "red")
            return

        subject = self.entry_subject.get().strip()
        # Sustituir marcadores de fecha antes de enviar
        body = replace_placeholders(self.text_body.get("1.0", tk.END).strip())
        smtp_password = self.smtp_pwd_var.get()

        # Bloquear el botón mientras se envía
        self._sending = True
        self.btn_send.config(state=tk.DISABLED)
        self._set_status(t("status_sending"), "blue")

        # Lanzar hilo secundario para no congelar la ventana
        t_thread = threading.Thread(
            target=self._send_in_background,
            args=(recipients, subject, body, selected_account, smtp_password),
            daemon=True,  # El hilo muere si la ventana se cierra
        )
        t_thread.start()

    def _send_in_background(
        self,
        recipients: list,
        subject: str,
        body: str,
        selected_account: str,
        smtp_password: str,
    ) -> None:
        """
        Hilo secundario: ejecuta el envío y devuelve el resultado al hilo principal
        mediante root.after() (único método thread-safe para actualizar la UI en Tkinter).

        Elige el método de envío según el tipo de cuenta:
          - Cuenta personal (Hotmail, Gmail) → SMTP directo
          - Cuenta empresarial (Exchange/O365) → Outlook COM
        """
        try:
            if is_personal_account(selected_account):
                # ── SMTP para cuentas personales ──────────────────────────────
                smtp_cfg = get_smtp_config(selected_account)
                if not smtp_cfg:
                    raise EmailSendError(
                        f"No hay configuración SMTP para el dominio de '{selected_account}'."
                    )
                if not smtp_password:
                    raise EmailSendError(t("status_smtp_pwd_required"))

                smtp_server, smtp_port = smtp_cfg
                send_via_smtp(
                    from_email=selected_account,
                    recipients=recipients,
                    subject=subject,
                    body=body,
                    password=smtp_password,
                    smtp_server=smtp_server,
                    smtp_port=smtp_port,
                )
            else:
                # ── COM de Outlook para cuentas empresariales ─────────────────
                send_via_outlook_com(
                    recipients=recipients,
                    subject=subject,
                    body=body,
                    account_smtp=selected_account,
                )

            # Notificar éxito al hilo principal (thread-safe)
            self.root.after(0, self._on_send_success)

        except EmailSendError as exc:
            self.root.after(0, self._on_send_error, str(exc))
        except Exception as exc:
            self.root.after(0, self._on_send_error, str(exc))

    def _on_send_success(self) -> None:
        """Maneja el éxito del envío: actualiza estado y programa cierre si aplica."""
        self._sending = False
        self.btn_send.config(state=tk.NORMAL)

        if self.auto_close_var.get():
            delay = self._get_delay_secs()
            self._set_status(t("status_sent_closing", seconds=delay), "green")
            # Programar el cierre de la ventana en el hilo principal
            self.root.after(delay * 1000, self.root.destroy)
        else:
            self._set_status(t("status_sent"), "green")

    def _on_send_error(self, error_msg: str) -> None:
        """Maneja el fallo del envío: muestra el error y reactiva el botón Enviar."""
        self._sending = False
        self.btn_send.config(state=tk.NORMAL)
        self._set_status(t("status_error", error=error_msg), "red")
        logger.error("Error al enviar correo: %s", error_msg)

    # ── Punto de entrada ───────────────────────────────────────────────────────

    def run(self) -> None:
        """Inicia el bucle de eventos de Tkinter (bloqueante hasta que se cierra la ventana)."""
        self.root.mainloop()
