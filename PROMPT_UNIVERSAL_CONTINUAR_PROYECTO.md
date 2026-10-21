# PROMPT UNIVERSAL: CONTINUAR CUALQUIER PROYECTO DE AGY CLI EN ESCRITORIO

> **Instrucciones para el usuario:**
> Copia y pega el bloque a continuación en cualquier conversación nueva de la **aplicación de escritorio de Antigravity** cuando quieras continuar trabajando en un proyecto que iniciaste o modificaste desde la terminal con `agy cli`.
> Funciona para **cualquier carpeta o entorno de trabajo**, no solo este.

---

```markdown
Hola. Quiero continuar en esta aplicación de escritorio el trabajo que estaba realizando previamente en la terminal con `agy cli`.

Por favor, realiza el siguiente procedimiento de sincronización automática de contexto para este espacio de trabajo:

1. **Identifica el espacio de trabajo actual:**
   - Revisa la ruta actual del workspace o proyecto en el que estamos trabajando.
   - Si existe un archivo de contexto local (como `CONTEXTO_*.txt`, `bitacora*.md` o `README.md`), léelo primero.

2. **Recupera el historial de `agy cli`:**
   - Consulta la base de datos de sesiones de la CLI en:
     `~/.gemini/antigravity-cli/conversation_summaries.db`
   - Busca la última conversación correspondiente a esta carpeta/workspace (usando `workspace_uris` ordenado por `last_modified_time DESC`).
   - Lee el registro de la conversación en:
     `~/.gemini/antigravity-cli/brain/<conversation_id>/.system_generated/logs/transcript.jsonl` (o `history.jsonl`) para extraer:
     * El objetivo principal del usuario.
     * Los archivos creados o modificados.
     * Entornos virtuales (`.venv`), dependencias instaladas y configuraciones especiales.
     * Errores resueltos y comandos probados.

3. **Verifica el estado del entorno:**
   - Inspecciona `git status` (si es un repositorio).
   - Revisa si existen entornos virtuales activos o scripts ejecutables (`.sh`, `.py`).
   - Si el proyecto usa servicios locales (como Ollama, Docker o bases de datos), verifica su disponibilidad.

4. **Dame un reporte de continuación:**
   - Un resumen muy conciso de lo que se hizo en la terminal.
   - El estado exacto en el que dejamos el proyecto.
   - Las opciones o siguientes pasos recomendados para continuar trabajando desde aquí.
```

---

## ¿Por qué este prompt es universal?
1. **Detección Dinámica:** No depende de un ID de conversación fijo ni de una carpeta específica. La IA detecta la carpeta donde la abras.
2. **Conexión Directa CLI -> GUI:** La IA lee directamente la base de datos interna de `agy cli` (`~/.gemini/antigravity-cli/conversation_summaries.db`), reconstruyendo el historial exacto de lo que hablaste en la terminal.
3. **Cero configuraciones manuales:** No tienes que copiar y pegar historiales manualmente ni recordar qué comandos ejecutaste; la IA de escritorio lo lee todo por sí misma.
