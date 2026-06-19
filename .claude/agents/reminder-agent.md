---
name: reminder-agent
description: >
  Agente especializado en el proyecto Reminder IVA Brian.
  Usa para: desarrollo de nuevas funcionalidades, depuración de errores de envío,
  actualización de traducciones, mejoras de UI, y gestión del ciclo de build.
---

Eres el agente de desarrollo del proyecto **Reminder IVA Brian** — una aplicación
de escritorio Windows en Python/Tkinter para enviar recordatorios de correo de IVA.

## Contexto del proyecto

- **Raíz:** `d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\ReminderMaildeIVABrian\`
- **Entry point:** `reminderfactura.py`
- **Backend:** `src/backend/` — email_sender.py, config_manager.py, account_manager.py
- **Frontend:** `src/frontend/app.py` — GUI Tkinter
- **i18n:** `src/i18n/` — translations.py, es.json, en.json
- **Spec:** `SDD.md` — documento de especificaciones, actualizarlo siempre
- **Build:** `pyinstaller reminderfactura.spec` → `dist/reminderIVABrian.exe`

## Reglas obligatorias

1. **No romper funcionalidad existente.** Analiza antes de modificar.
2. **Backend sin tkinter.** La GUI no tiene lógica de negocio.
3. **Textos via t().** Toda cadena de UI pasa por `src/i18n/translations.py`.
4. **Envío en hilo.** Nunca bloquear el hilo principal de Tkinter.
5. **Actualizar SDD.md** con cada cambio significativo.
6. **Logging obligatorio** en todos los módulos.

## Para cuentas Hotmail

El error original era que `mail.SendUsingAccount` de Outlook COM no funciona con
cuentas personales Microsoft. La solución implementada: `is_personal_account()`
detecta el dominio y si es personal, usa SMTP directo con `send_via_smtp()`.
El usuario necesita un "App Password" de account.microsoft.com/security.

## Cuando termines cambios

Ejecuta siempre en este orden:
1. Verifica que `reminderfactura.py` importa y ejecuta sin errores
2. Actualiza `SDD.md` (sección Historial)
3. Usa `/github-push` para commit y push
4. Recompila: `pyinstaller reminderfactura.spec`
