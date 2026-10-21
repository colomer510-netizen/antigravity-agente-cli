# MEMORIA DEL PROYECTO: ANTIGRAVITY SDK + OLLAMA LOCAL

## Contexto del Proyecto
- **Propósito:** Ejecutar agentes con Google Antigravity SDK utilizando modelos locales de Ollama con máxima fluidez.
- **Carpeta del Proyecto:** `/home/enoc-colomer/Descargas/Antigravity_SDK`
- **Repositorio oficial:** `/home/enoc-colomer/Descargas/Antigravity_SDK/antigravity-sdk-python`
- **Entorno Virtual Python:** `/home/enoc-colomer/Descargas/Antigravity_SDK/.venv` (paquete `google-antigravity==0.1.20`)
- **Backend Ollama:** `http://localhost:11434/v1`
  - Modelo por defecto: `llama3.2:latest`
  - Modelo alternativo: `phi4-mini:latest`
- **Configuración de Código:**
  ```python
  from google.antigravity import Agent, LocalOpenAIAgentConfig

  config = LocalOpenAIAgentConfig(
      base_url="http://localhost:11434/v1",
      model="llama3.2:latest",
  ).lightweight()
  ```
- **Lanzadores y Comandos:**
  - Comando global en cualquier terminal: `agente sdk`
  - Script interactivo: `chat_ollama.py`
  - Lanzador bash: `iniciar_agente.sh`
- **Detalle completo de la sesión:** Ver `CONTEXTO_CONVERSACION.txt`
