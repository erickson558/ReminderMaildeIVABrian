---
description: Agrega comentarios explicativos a cada parte del código Python del proyecto
---

Revisa todos los archivos Python en `src/` y `reminderfactura.py` y agrega comentarios
que expliquen QUÉ HACE cada sección importante del código.

## Instrucciones

### ¿Qué comentar?

Agrega comentarios cuando el código no sea autoevidente:
- **Bloques de lógica compleja** — explica el algoritmo o la decisión de diseño
- **Llamadas a APIs externas** — explica qué hace y por qué (ej. `win32.Dispatch`)
- **Casos especiales** — condiciones no obvias, edge cases
- **Configuración importante** — constantes, valores por defecto con razón de ser
- **Flujos de threading** — explicar por qué se usa hilo secundario

### ¿Qué NO comentar?

- No comentar lo que el nombre ya dice (no: `# crea el botón` sobre `tk.Button(...)`)
- No parafrasear el código línea a línea
- No poner docstrings de varios párrafos en funciones simples

### Formato preferido

```python
# ── Título de sección ──────────────────────────────────────────────────────────
# Explicación breve si la sección hace algo no obvio

def funcion(param):
    """Una línea que describe QUÉ hace, no CÓMO."""
    # Comentario inline sólo cuando el WHY no es obvio
    resultado = alguna_logica_compleja(param)
    return resultado
```

## Archivos a revisar

1. `src/backend/email_sender.py` — el más importante (lógica de envío dual)
2. `src/backend/account_manager.py`
3. `src/backend/config_manager.py`
4. `src/i18n/translations.py`
5. `src/frontend/app.py` — threading pattern especialmente
6. `reminderfactura.py`

## Después de comentar

Actualiza el `SDD.md` si los comentarios revelan algo importante de la arquitectura.
