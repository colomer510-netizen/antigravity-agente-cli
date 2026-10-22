# Antigravity Agente CLI: Agente Autónomo Local para Linux (Ubuntu)

Un agente de terminal ligero, ultra-rápido y 100% offline para Linux (Ubuntu), potenciado por **Ollama** en CPU local y con integración de compatibilidad con **Google Antigravity SDK**.

Diseñado específicamente para funcionar con máxima fluidez y bajo consumo de recursos incluso en ordenadores antiguos o de especificaciones modestas (desde 4 GB de RAM y procesadores de 2 a 4 núcleos), sin requerir GPU dedicada ni depender de servicios en la nube.

---

## ⚡ Características Principales

- **Velocidad y respuesta instantánea en CPU:** Respuestas en 1 a 2 segundos utilizando modelos ligeros como `qwen2.5-coder:1.5b` (~986 MB de RAM) o `llama3.2:3b`.
- **Doble capa de seguridad inteligente:**
  - **Auto-ejecución transparente:** Comandos seguros de consulta y diagnóstico (`uname`, `free`, `df`, `uptime`, `lsblk`, `ps`, `sensors`, etc.) se ejecutan automáticamente en tiempo real sin interrumpir al usuario con preguntas innecesarias.
  - **Menú interactivo de confirmación [1-4]:** Cualquier comando que modifique el sistema, elimine archivos (`rm`), formatee particiones (`mkfs`, `dd`) o afecte el encendido (`reboot`, `poweroff`) activa un menú de confirmación con advertencias visuales de alto riesgo.
- **Auditoría del sistema sin alucinaciones:** Obligación estricta al modelo de consultar comandos reales antes de responder sobre memoria RAM, disco, kernel o carga.
- **Explorador y buscador de comandos integrado:** Recetas integradas para `compgen -c`, `whatis`, `apropos`, `fzf`, `help` y el gestor `adm`.
- **Tuberías y argumentos directos:** Soporta ejecución conversacional interactiva, argumentos de una sola línea (`agente "pregunta"`) y pipes Unix (`cat archivo | agente "analiza"`).
- **Historial persistente con flechas ↑ / ↓:** Navegación por el historial de preguntas anteriores mediante `readline`.

---

## 🚀 Optimización para PCs de Bajos Recursos (Low-Resource Tuning)

El agente incorpora salvaguardas arquitectónicas diseñadas para no saturar la CPU ni la memoria:

| Parámetro | Configuración | Beneficio en hardware modesto |
| :--- | :--- | :--- |
| **Presupuesto dinámico de hilos** | `max(1, min(4, CPU_COUNT - 1))` | Deja siempre al menos 1 núcleo libre para el sistema operativo y la interfaz gráfica; nunca congela la máquina. |
| **Ventana de contexto (`num_ctx`)** | `2048` tokens | Reduce el uso de RAM del KV-cache a menos de 1 GB. |
| **Límite de generación (`num_predict`)** | `192` tokens | Evita bucles de generación desmedidos y acelera el tiempo de inferencia. |
| **Persistencia caliente (`keep_alive`)** | `30m` | Mantiene el modelo en memoria RAM para evitar tiempos de recarga desde el disco. |
| **Truncado de salida de comandos** | 16 líneas (`MAX_OUTPUT_LINES`) | Evita enviar salidas masivas de texto al evaluador de prompts de la CPU. |
| **Ventana deslizante de historial** | 4 turnos (`MAX_TURNS_HISTORY`) | Limita el tamaño del prompt conservando la memoria inmediata de la sesión. |

---

## 📦 Requisitos e Instalación

### 1. Prerrequisitos
- Sistema Operativo: Linux (Ubuntu / Debian o derivados).
- Python 3.10 o superior.
- [Ollama](https://ollama.com/) instalado y en ejecución (`systemctl status ollama` o `ollama serve`).

### 2. Descargar modelo recomendado
Para computadores con pocos recursos (4 GB a 8 GB de RAM):
```bash
ollama run qwen2.5-coder:1.5b
# O alternativamente:
ollama run llama3.2:latest
```

### 3. Instalación de dependencias
Clona el repositorio con sus submódulos:
```bash
git clone --recurse-submodules https://github.com/colomer510-netizen/antigravity-agente-cli.git
cd antigravity-agente-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Lanzador global de terminal
Crea un enlace simbólico o script en `~/.local/bin/agente`:
```bash
ln -s "$(pwd)/chat_ollama.py" ~/.local/bin/agente
chmod +x ~/.local/bin/agente
```

---

## 💡 Ejemplos de Uso

### Modo Interactivo
```bash
agente
```
```text
============================================================
🤖 Agente Inteligente Local con Ollama
============================================================
• Endpoint   : http://localhost:11434/v1
• Modelo     : enoc-agent:latest
• Hardware   : 4 CPUs detectados (3 hilos optimizados para baja latencia)
• SO         : Linux (Ubuntu)
• Navegación : Historial con flechas ↑ / ↓
• Comandos   : '/modelos', '/limpiar', '/ayuda', 'salir'
============================================================

Tú > cómo está mi sistema

Agente > Consultando memoria RAM...

🔍 Ejecutando automáticamente: free -h

Agente > Revisando disco...

🔍 Ejecutando automáticamente: df -h /

Agente > Tu sistema está así:
• RAM: 14 GB total, 5.6 GB en uso, 7.0 GB disponibles.
• Disco (/): 233 GB total, 160 GB usados (74%), 62 GB libres.
Todo funciona con normalidad.
```

### Consulta directa
```bash
agente "cuál es mi kernel y mi IP privada"
```

### Entrada por tubería (Pipe)
```bash
git status | agente "resume los cambios pendientes de forma concisa"
```

---

## 🧪 Pruebas Automatizadas

El proyecto cuenta con una suite de pruebas unitarias sin dependencias externas obligatorias:

```bash
# Ejecutar con el módulo nativo unittest:
python3 -m unittest discover tests

# O ejecutar con pytest (si está instalado):
pytest tests/
```

Todas las pruebas validan:
- Auto-ejecución correcta de comandos seguros de lectura.
- Bloqueo y menú de confirmación para comandos de riesgo.
- Rechazo de alucinaciones o comandos desconocidos.
- Extracción limpia de comandos `CMD:` sin colisiones con bloques de código explicativos.
- Parámetros de bajo consumo y truncamiento de salidas extensas.

---

## ⚖️ Licencia y Atribución

Este proyecto está licenciado bajo la **Licencia Apache 2.0** (Apache License, Version 2.0). Consulta el archivo [LICENSE](LICENSE) para más detalles.

De conformidad con la Sección 4(d) de la Licencia Apache 2.0, se incluye el archivo [NOTICE](NOTICE) reconociendo formalmente la atribución al proyecto [Google Antigravity SDK](https://github.com/google/antigravity), desarrollado por Google LLC.
