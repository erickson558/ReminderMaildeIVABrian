# SDD — Spec Driven Development: Reminder IVA Brian

> Documento vivo. Actualizar antes de cada cambio significativo y en cada commit.

---

## 1. Descripción del proyecto

Aplicación de escritorio Windows que envía recordatorios de correo electrónico
para el seguimiento del Formulario IVA de Brian (pagos ISR/IVA del 10 al 15 de cada mes).

**Plataforma:** Windows 10/11  
**UI:** Tkinter (Python stdlib)  
**Distribución:** Ejecutable autónomo (.exe) generado con PyInstaller

---

## 2. Problema original y solución

| Problema | Causa | Solución implementada |
|---|---|---|
| Hotmail no enviaba y daba error | `mail.SendUsingAccount` de Outlook COM falla para cuentas personales Microsoft | Detección automática de dominio + envío SMTP directo con STARTTLS |
| GUI se podía congelar al enviar | Envío en hilo principal bloqueaba Tkinter | Envío movido a `threading.Thread` |
| Sin internacionalización | Todos los textos hardcoded en español | Motor i18n con JSON por idioma (`es.json`, `en.json`) |
| Sin modularidad | Todo en un único archivo de 230 líneas | Separación frontend / backend / i18n |

---

## 3. Arquitectura

```
reminderfactura.py          ← Punto de entrada (thin wrapper + logging)
│
src/
├── backend/
│   ├── config_manager.py   ← Lectura/escritura de config.json
│   ├── account_manager.py  ← Descubrimiento de cuentas Outlook + detección de tipo
│   └── email_sender.py     ← Envío via COM (Exchange) o SMTP (Hotmail/Gmail)
│
├── frontend/
│   └── app.py              ← GUI Tkinter; delega TODO al backend
│
└── i18n/
    ├── translations.py     ← Motor t() + load_language()
    ├── es.json             ← Cadenas en español
    └── en.json             ← Cadenas en inglés
```

---

## 4. Especificaciones funcionales

### 4.1 Envío de correo

- **Exchange / Office 365 empresarial:** Outlook COM (`win32com.client`).
- **Hotmail / Outlook.com / Gmail / Yahoo:** SMTP directo, puerto 587, STARTTLS.
- **Detección automática:** basada en el dominio de la cuenta seleccionada.
- **Placeholders en cuerpo:** `[Mes en letras]` → mes en español; `[año en numero]` → año.
- **Filtrado:** el remitente se excluye automáticamente de la lista de destinatarios.

### 4.2 Interfaz de usuario

- Gestión de destinatarios (agregar / eliminar, selección múltiple).
- Campo de asunto y cuerpo con scroll.
- Combobox de cuentas (cargado desde Outlook).
- Campo App Password visible con texto de ayuda (para Hotmail/Gmail).
- Aviso naranja cuando se detecta cuenta personal.
- Cierre automático configurable tras envío exitoso.
- Selector de idioma (Español / English) — reconstruye la UI sin perder datos.
- Botón "Cómprame una cerveza" (enlace PayPal).
- Barra de estado con mensajes de color.

### 4.3 Configuración persistida (`config.json`)

| Campo | Tipo | Descripción |
|---|---|---|
| `destinatarios` | `string[]` | Lista de correos destinatarios |
| `asunto` | `string` | Asunto del correo |
| `cuerpo` | `string` | Cuerpo del correo |
| `auto_close` | `bool` | Cerrar app tras enviar |
| `auto_close_delay` | `int` | Segundos antes de cerrar |
| `smtp_password` | `string` | App Password para SMTP |
| `language` | `string` | Código de idioma ("es"/"en") |
| `selected_account` | `string` | Última cuenta de envío |

- Si `config.json` cambia externamente mientras la app está abierta, los destinatarios se recargan automáticamente antes del siguiente envío.

---

## 5. Reglas de calidad

- El backend NO importa nada de `tkinter`.
- La GUI NO contiene lógica de negocio.
- Todos los textos de UI pasan por `t()`.
- El envío siempre corre en un hilo secundario.
- Nunca usar `except:` (bare) — siempre capturar excepciones específicas.
- Logging en todos los módulos con `logger = logging.getLogger(__name__)`.

---

## 6. Build a .exe

```bash
# Instalar dependencias
pip install -r requirements.txt

# Compilar (genera dist/reminderIVABrian.exe)
pyinstaller reminderfactura.spec
```

El .exe resultante:
- No muestra consola.
- Incluye traducciones JSON y el icono `reminderagua.ico`.
- Guarda `config.json` y `reminder.log` junto al .exe.

---

## 7. Roadmap / Backlog

- [ ] Soporte HTML en el cuerpo del correo.
- [ ] Múltiples perfiles de configuración.
- [ ] Adjuntos de archivos.
- [ ] Programación interna de envío (sin Task Scheduler externo).
- [ ] Más idiomas (portugués, francés).

---

## 8. Historial de cambios

| Fecha | Cambio |
|---|---|
| 2026-06-20 | Fix de destinatarios: la app ahora recarga `config.json` antes de enviar si el archivo cambió externamente y normaliza correos duplicados o con espacios. |
| 2026-06-19 | Refactor completo: separación frontend/backend, fix Hotmail (SMTP), i18n, threading, botón donación, SDD, agents/skills |
