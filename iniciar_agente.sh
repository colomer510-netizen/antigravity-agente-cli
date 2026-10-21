#!/usr/bin/env bash
# Script para iniciar Antigravity SDK con Ollama
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"

# Puedes pasar el modelo como argumento, por ejemplo:
# ./iniciar_agente.sh phi4-mini:latest
# Por defecto usa phi4-mini:latest que está instalado localmente
MODEL="${1:-phi4-mini:latest}"

python3 "$SCRIPT_DIR/chat_ollama.py" "$MODEL"
