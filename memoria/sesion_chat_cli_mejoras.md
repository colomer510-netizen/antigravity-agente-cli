---
name: Sesión de Mejoras al Agente CLI y Control de Versiones
description: Registro histórico de la sesión donde se eliminó ChatGPT de escritorio, aichat y se potenció el agente nativo
preguntas:
  - ¿Por qué se eliminó la app de escritorio de ChatGPT y aichat?
  - ¿Qué mejoras se implementaron en la versión v1.0.0 del agente?
  - ¿Cómo se evitó la saturación de CPU en modelos locales?
---

# Sesión: Evolución del Agente CLI Local a v1.0.0

Registro de decisiones técnicas tomadas durante la sesión del 20 de Octubre de 2026.

## 1. Desinstalación y Limpieza
- **ChatGPT Desktop y Codex CLI:** Se detectó que el binario de Codex embebido en el paquete deb requería un runtime no soportado de daemon. Se eliminó el enlace, se purgó el paquete `chatgpt` de Ubuntu y se borró el acceso PWA residual en `~/.local/share/applications/chrome-kmhihenpidpfcamajppbdjcdbfloogol-Default.desktop`.
- **aichat:** Se desinstaló y eliminó `~/.config/aichat` debido a que fallaba al ejecutar comandos bash cuando el modelo incluía texto conversacional antes de `CMD:`.

## 2. Desarrollo del Agente Propio (`agente`)
Ubicación del repositorio: `/home/enoc-colomer/dev/personal/antigravity-sdk`

### Hitos en Git:
- `ab03b3f`: Versión base inicial preservada.
- `f86158e` (Tag `v1.0.0`): Incorporación de `readline` (flechas ↑/↓), soporte para pipes de Linux, recetas anti-alucinaciones de red/sistema y detector visual de comandos destructivos.
- `d94c146`: Optimización de rendimiento mediante **Ventana Deslizante de Memoria** (`podar_historial`) y compactación de salidas extensas de comandos para evitar sobrecarga en la CPU de la laptop.

## 3. Conexiones
- Conectado con [[INDICE]]
- Archivo fuente: `/home/enoc-colomer/dev/personal/antigravity-sdk/chat_ollama.py:250`
