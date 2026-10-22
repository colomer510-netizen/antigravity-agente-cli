# Memoria de Sesión: Herramientas de Dictado por Voz y Repositorios de Memoria Persistente

- **Fecha:** 2026-10-21
- **Usuario:** Enoc
- **Contexto:** Investigación, descarga y organización de soluciones para dictado por voz offline en Linux y servidores MCP / frameworks de memoria persistente para LLMs y agentes.

---

## 1. Dictado por Voz en Linux (Reemplazo de Win + H / Android)

### Opciones identificadas y descargadas:
1. **Handy** (`Handy_0.9.8_amd64.deb`):
   - La opción más moderna para Linux (Rust/Tauri).
   - Utiliza Whisper localmente con aceleración GPU/Vulkan.
   - Atajo push-to-talk o toggle para pegar texto automáticamente en cualquier aplicación activa.
2. **Vocalinux** (`vocalinux_0.18.4-1_amd64.deb`):
   - Dictado nativo especializado en Linux con soporte para X11 y Wayland.
   - Motores configurables entre `whisper.cpp` y VOSK.
3. **BlahST** (`QuantiusBenignus/BlahST`):
   - Herramienta rápida de terminal para dictado por teclado global basada en `whisper.cpp` con integración opcional a `llama.cpp`.
4. **whisper.cpp** (`ggerganov/whisper.cpp`):
   - Motor central de alto rendimiento en C/C++ clonado para compilación local.

---

## 2. Repositorios de Memoria Persistente / Contexto MCP (Similares a Neuromapa)

### Repositorios clonados:
1. **mem0** (`mem0ai/mem0`):
   - Memoria a largo plazo para agentes de IA. Soporta integración local con Ollama y conector MCP.
2. **local-memory-mcp** (`cunicopia-dev/local-memory-mcp`):
   - Servidor MCP 100% local basado en SQLite y búsqueda vectorial (FAISS/pgvector) sin depender de APIs de terceros.
3. **memori-mcp** (`MemoriLabs/memori-mcp`):
   - Memoria para agentes enfocada en registrar ejecuciones de herramientas, decisiones, comandos de terminal y artefactos.

---

## 3. Ubicación de Archivos en Disco

Todas las descargas y repositorios de esta sesión quedaron concentrados en:
- Ruta: `/home/enoc-colomer/Descargas/Herramientas_IA_Dictado_Memoria/`
  - `Handy_0.9.8_amd64.deb`
  - `vocalinux_0.18.4-1_amd64.deb`
  - `BlahST/`
  - `whisper.cpp/`
  - `mem0/`
  - `local-memory-mcp/`
  - `memori-mcp/`
