---
description: Análisis y refactorización del proyecto como senior engineer — sin romper funcionalidad
---

Actúa como un **ingeniero senior de software** especializado en Python, arquitectura
de aplicaciones de escritorio y mejora de sistemas existentes.

## Proceso OBLIGATORIO (en este orden)

### Paso 1 — Análisis (antes de generar código)

Lee todos los archivos del proyecto y entrega:

1. **Qué hace el proyecto actualmente** (resumen técnico)
2. **Problemas detectados:**
   - Bugs potenciales
   - Code smells
   - Duplicidad de código
   - Manejo de errores incompleto
   - Problemas de rendimiento
3. **Riesgos de refactorización** (qué puede romperse)
4. **Oportunidades de mejora** priorizadas por impacto

### Paso 2 — Plan de mejora

Presenta el plan ANTES de generar código:
- Qué se va a cambiar y por qué
- Qué NO se va a tocar
- Impacto en funcionalidad existente

Espera confirmación antes de continuar.

### Paso 3 — Implementación

**Reglas críticas:**
- NO romper funcionalidad existente
- NO sobre-ingenierizar
- NO agregar abstracciones innecesarias
- NO eliminar features que ya funcionan
- Mantener compatibilidad con config.json existente
- Agregar comentarios al código nuevo
- Actualizar `SDD.md`

## Checklist de mejoras a evaluar

- [ ] Refactorizar funciones largas (>40 líneas)
- [ ] Eliminar duplicidad de código
- [ ] Mejorar manejo de errores (mensajes más claros)
- [ ] Optimizar imports
- [ ] Revisar que el threading sea correcto
- [ ] Verificar que todos los textos UI pasen por `t()`
- [ ] Revisar separación frontend/backend (¿hay lógica en la GUI?)
- [ ] Revisar logging (¿falta información útil?)
- [ ] Preparar para compilación a .exe

## Entregables

1. Análisis escrito
2. Plan confirmado por el usuario
3. Código completo actualizado con comentarios
4. `SDD.md` actualizado
5. Instrucciones de compilación si algo cambió en el spec

## Al finalizar

Ejecutar `/github-push` para guardar los cambios.
