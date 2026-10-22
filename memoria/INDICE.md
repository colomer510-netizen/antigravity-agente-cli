---
name: Índice de Memoria de Antigravity SDK y Agente CLI
description: Mapa y neurona central de memoria viva para el desarrollo del agente local inteligente
preguntas:
  - ¿Dónde está el script del agente y cómo se ejecuta?
  - ¿Qué arquitectura y optimizaciones tiene el agente local de Ollama?
  - ¿Qué historial de versiones y git tiene este proyecto?
---

# Memoria de Antigravity SDK & Agente CLI Local

Neurona principal que documenta la arquitectura, el diseño y las optimizaciones de rendimiento del agente de consola local de Enoc.

## Conexiones y Referencias
- [[sesion_chat_cli_mejoras]] - Bitácora de la sesión de desinstalación de ChatGPT/aichat y evolución del agente a v1.0.0.
- [[handoff_cierre_sesion]] - Estado de consolidación y próximos pasos de desarrollo.
- [[2026-10-21_dictado_y_memorias_mcp]] - Investigación y descarga de herramientas de dictado por voz y memoria persistente MCP.
- Código fuente del agente: `/home/enoc-colomer/dev/personal/antigravity-sdk/chat_ollama.py:1`
- Wrapper ejecutable global en PATH: `/home/enoc-colomer/.local/bin/agente:1`
- Protocolo de memoria viva: `/home/enoc-colomer/dev/mcp/neuromapa/PROTOCOLO_MEMORIA_NEUROMAPA.md`

## Componentes Clave
1. **Script Central (`chat_ollama.py`):**
   - Conexión asíncrona streaming con Ollama (`http://localhost:11434/v1`).
   - Bucle de agente autónomo multi-paso (`MAX_AGENT_STEPS = 4`) con encadenamiento de comandos.
   - Auto-ejecución directa de comandos seguros de solo lectura (`df`, `free`, `uptime`, `sensors`, `uname`, etc.).
   - Modo de ejecución interactivo y por tuberías (`pipe`).
   - Ventana deslizante de memoria (`podar_historial`) para mantener consumo mínimo de CPU.
   - Truncador de salidas largas (`compactar_salida_comando`).
   - Control de ejecución interactivo `[1-4]` con alertas rojas en comandos peligrosos.
2. **Entorno Virtual (`.venv`):**
   - Python con `httpx` y soporte nativo de `readline`.
3. **Suite de Pruebas y Calidad:**
   - Pruebas unitarias en `tests/test_agente.py` (8/8 pasando al 100%).
   - CI automatizado en `.github/workflows/quality-ci.yml`.
   - Código auditado con 0 errores de estilo/sintaxis via Ruff (`code-guardian`).
4. **Optimización de Hardware (Bajos Recursos):**
   - Presupuesto dinámico de hilos CPU (`OPTIMAL_THREADS`), `num_ctx: 2048`, `keep_alive: "30m"`.
5. **Licencia y Atribución:**
   - Licencia pública Apache 2.0 (`LICENSE`) con archivo de atribución `NOTICE` al Google Antigravity SDK.
