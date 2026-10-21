# PROMPT PARA CONTINUAR ESTE PROYECTO EN ANTIGRAVITY

Copia y pega el siguiente bloque de texto en el chat de Antigravity (en la aplicación de escritorio o en la terminal) cada vez que abras una nueva conversación y quieras retomar este proyecto con todo su contexto:

---

```markdown
Hola. Estamos trabajando en el proyecto de integración de **Google Antigravity SDK con Ollama local**.

Por favor, lee el archivo de contexto del proyecto ubicado en:
`/home/enoc-colomer/Descargas/Antigravity_SDK/CONTEXTO_CONVERSACION.txt`

### Resumen del estado actual del proyecto:
1. **Ubicación:** `/home/enoc-colomer/Descargas/Antigravity_SDK`
2. **Repositorio:** `antigravity-sdk-python` clonado en esa carpeta.
3. **Entorno Virtual:** `.venv` activo con `google-antigravity==0.1.20` instalado.
4. **Backend Local:** Ollama (`http://localhost:11434/v1`) con los modelos `llama3.2:latest` y `phi4-mini:latest`.
5. **Configuración de fluidez:** Usa `LocalOpenAIAgentConfig` con `.lightweight()` para evitar saturación de CPU/RAM.
6. **Comando Global de Terminal:** `agente sdk` (creado en `~/.local/bin/agente`).
7. **Scripts disponibles:**
   - `chat_ollama.py`: chat interactivo con el SDK y Ollama.
   - `iniciar_agente.sh`: lanzador bash rápido.

Por favor, confirma que tienes este contexto claro y dime qué pasos o mejoras podemos implementar a continuación.
```

---

## Instrucciones adicionales para el usuario:
- Si abres la carpeta del proyecto en Antigravity Escritorio, puedes simplemente arrastrar el archivo `CONTEXTO_CONVERSACION.txt` al chat o escribir `@CONTEXTO_CONVERSACION.txt` junto con el prompt anterior.
- El agente sabrá exactamente dónde está todo y cómo seguir desarrollando sin empezar desde cero.
