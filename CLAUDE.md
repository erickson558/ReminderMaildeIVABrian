# CLAUDE.md — Instrucciones del proyecto para Claude Code

## Proyecto
Reminder IVA Brian — Aplicación de escritorio Windows para enviar recordatorios de correo.

## Stack
- Python 3.x + Tkinter (GUI)
- pywin32 (Outlook COM para Exchange)
- smtplib stdlib (SMTP para Hotmail/Gmail)
- PyInstaller (compilación a .exe)

## Estructura
```
src/backend/     → lógica de negocio (NO importar tkinter aquí)
src/frontend/    → GUI Tkinter (NO lógica de negocio aquí)
src/i18n/        → traducciones JSON + motor t()
reminderfactura.py → entry point (thin)
```

## Reglas de código
- Todos los textos de UI deben usar `t("clave")` de `src/i18n/translations.py`.
- El envío de correo siempre va en `threading.Thread` — no bloquear la GUI.
- Actualizar `SDD.md` (sección Historial) en cada cambio significativo.
- Probar tanto con cuenta Exchange (Outlook COM) como con Hotmail (SMTP).

## Compilación
```bash
pyinstaller reminderfactura.spec
# Resultado: dist/reminderIVABrian.exe
```

## GitHub
- Cuenta: erickson558
- Protocolo: https
- Usar `/github-push` para hacer commit y push.

## Skills disponibles
- `/github-push`     — commit + push al repositorio GitHub
- `/comment-code`    — agregar comentarios explicativos al código
- `/senior-refactor` — análisis y refactorización estilo senior engineer
