---
description: Commit todos los cambios y hace push al repositorio GitHub (cuenta erickson558)
---

Ejecuta el flujo completo de commit y push para este proyecto.

## Pasos

1. **Verificar estado del repositorio**
   ```bash
   git status
   git diff --stat
   ```

2. **Inicializar git si no existe**
   Si no hay repositorio `.git`, ejecutar:
   ```bash
   git init
   git branch -M main
   ```

3. **Verificar/crear repositorio remoto en GitHub**
   Usando la cuenta `erickson558` (ya autenticada en gh CLI):
   ```bash
   gh repo view erickson558/ReminderMaildeIVABrian 2>/dev/null || \
   gh repo create ReminderMaildeIVABrian --public --description "Reminder IVA Brian - Aplicación de recordatorio de correo para IVA" --source=. --remote=origin
   ```

4. **Agregar archivos al staging (excluir binarios y build)**
   ```bash
   git add reminderfactura.py reminderfactura.spec requirements.txt
   git add config.json CLAUDE.md SDD.md
   git add src/
   git add .claude/
   git add .gitignore
   ```

5. **Crear .gitignore si no existe**
   ```gitignore
   # Build artifacts
   build/
   dist/
   *.exe
   *.spec.bak
   
   # Python
   __pycache__/
   *.pyc
   *.pyo
   .venv/
   
   # Logs
   reminder.log
   
   # IDE
   .vscode/
   ```

6. **Crear commit descriptivo**
   ```bash
   git commit -m "feat: refactor completo — fix Hotmail SMTP, i18n, threading, donate btn"
   ```

7. **Push al remoto**
   ```bash
   git push -u origin main
   ```

8. **Confirmar con la URL del repositorio**

## Notas
- Cuenta GitHub: `erickson558` (autenticada via gh keyring)
- No incluir `dist/`, `build/`, ni `.exe` en el commit
- Si el repositorio ya existe, solo hacer `git push`
