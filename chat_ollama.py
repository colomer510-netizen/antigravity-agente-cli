#!/usr/bin/env python3
"""
Agente Inteligente Ultra-Rápido con Ollama y Control del Sistema Linux.
- Conexión directa streaming a través de Ollama.
- Mensaje breve de contexto antes de solicitar el comando.
- Menú interactivo de seguridad: [1-4] con advertencias de riesgo.
- Detección precisa de IP, red, hardware, procesos y tareas de código.
- Historial persistente en terminal con soporte de flechas ↑/↓ (readline).
- Soporte para pipes y comandos directos: echo "..." | agente "analiza" o agente "comando"
- Comandos internos: /modelos, /modelo, /limpiar, /historial, /ayuda, salir.
"""

import asyncio
import itertools
import json
import os
import re
import readline
import subprocess
import sys
import httpx

DEFAULT_MODEL = "qwen2.5-coder:1.5b"
BASE_URL = "http://localhost:11434/v1"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
HISTORIAL_PATH = os.path.expanduser("~/.config/antigravity_agente_history")

SYSTEM_PROMPT = """Eres el asistente técnico de Linux (Ubuntu) y programación de Enoc.
Tu misión es monitorear el sistema operativo, gestionar archivos/código y ejecutar tareas con precisión técnica real.

REGLAS ABSOLUTAS:
1. El sistema operativo es LINUX (Ubuntu), NUNCA Windows ni macOS. Jamás uses comandos de Windows (dir, cls, tasklist, etc.).
2. NUNCA inventes números, datos de red, IP, RAM, CPU o contenidos de archivos sin ejecutar un comando real de Linux.
3. Para ejecutar un comando bash en Linux, debes responder SIEMPRE en este formato exacto:
Una frase corta de contexto (1 a 4 palabras).
CMD: <comando bash>

RECETAS OBLIGATORIAS DE COMANDOS EN LINUX:
- IP Wi-Fi y tarjetas de red privadas: CMD: ip -br addr
- Router / Gateway / Puerta de enlace: CMD: ip route show default
- IP pública: CMD: curl -s https://ifconfig.me
- Almacenamiento / Disco: CMD: df -h /
- Memoria RAM: CMD: free -h
- Procesos con mayor consumo de RAM: CMD: ps aux --sort=-%mem | head -n 8
- Procesos con mayor consumo de CPU: CMD: ps aux --sort=-%cpu | head -n 8
- Temperatura y ventiladores: CMD: sensors
- Estado o carga de CPU: CMD: uptime
- Hardware / Batería: CMD: upower -i $(upower -e | grep 'BAT') 2>/dev/null || acpi 2>/dev/null
- Buscar archivos en el proyecto: CMD: find . -maxdepth 3 -not -path '*/.*'
- Leer código o archivo: CMD: cat <ruta_archivo>
- Inspeccionar git: CMD: git status -s
"""

# Comandos de alto riesgo para advertencia visual
DANGEROUS_PATTERNS = [
    r"\brm\s+-[rf]*\b",
    r"\bmkfs\b",
    r"\bdd\b",
    r">\s*/dev/sd[a-z]",
    r"\bchmod\s+-R\s+777\b",
    r"\bshutdown\b",
    r"\breboot\b"
]

SPINNER_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

class Spinner:
    def __init__(self, message: str = "Pensando..."):
        self.message = message
        self.running = False
        self.task = None

    async def _spin(self):
        spinner_cycle = itertools.cycle(SPINNER_CHARS)
        while self.running:
            char = next(spinner_cycle)
            sys.stdout.write(f"\r\033[1;36m{char}\033[0m {self.message}")
            sys.stdout.flush()
            await asyncio.sleep(0.08)
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    def start(self):
        self.running = True
        self.task = asyncio.create_task(self._spin())

    async def stop(self):
        if self.running:
            self.running = False
            if self.task:
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass

def setup_readline():
    """Habilita el historial persistente con navegación mediante flechas ↑ y ↓."""
    try:
        os.makedirs(os.path.dirname(HISTORIAL_PATH), exist_ok=True)
        if os.path.exists(HISTORIAL_PATH):
            readline.read_history_file(HISTORIAL_PATH)
        readline.set_history_length(1000)
    except Exception:
        pass

def save_readline():
    """Guarda el historial de comandos al cerrar la sesión."""
    try:
        readline.write_history_file(HISTORIAL_PATH)
    except Exception:
        pass

def es_comando_peligroso(cmd: str) -> bool:
    """Verifica si el comando contiene patrones potencialmente destructivos."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd):
            return True
    return False

def pedir_confirmacion_comando(cmd_propuesto: str) -> tuple[bool, str]:
    """Muestra el menú interactivo para aprobar, editar o cancelar un comando."""
    cmd_actual = cmd_propuesto
    while True:
        peligroso = es_comando_peligroso(cmd_actual)
        print("\n" + "=" * 58)
        if peligroso:
            print("🚨 \033[1;41;97m ATENCIÓN: COMANDO POTENCIALMENTE PELIGROSO \033[0m")
        print("⚙️  \033[1;33mEl Agente solicita ejecutar un comando en Linux:\033[0m")
        print(f"   \033[1;32m{cmd_actual}\033[0m")
        print("=" * 58)
        print("¿Qué deseas hacer?")
        print(" [1] Sí, ejecutar comando")
        print(" [2] Modificar comando manualmente")
        print(" [3] Dar otras instrucciones / feedback al agente")
        print(" [4] Cancelar")
        print("-" * 58)

        try:
            opcion = input("Selecciona una opción [1-4] (por defecto 1): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperación cancelada.")
            return False, "Comando cancelado por el usuario."

        if opcion in ("1", ""):
            print("\n▶️  Ejecutando en tu sistema...")
            try:
                res = subprocess.run(
                    cmd_actual,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=25
                )
                salida = res.stdout if res.returncode == 0 else (res.stderr or res.stdout)
                return True, salida.strip() or "(Comando ejecutado con éxito sin salida)"
            except subprocess.TimeoutExpired:
                return False, "Error: El comando tardó demasiado tiempo y fue cancelado."
            except Exception as e:
                return False, f"Error al ejecutar: {e}"

        elif opcion == "2":
            try:
                nuevo_cmd = input("\nEscribe el comando modificado: ").strip()
                if nuevo_cmd:
                    cmd_actual = nuevo_cmd
                else:
                    print("No ingresaste ningún comando, se mantiene el actual.")
            except (KeyboardInterrupt, EOFError):
                pass

        elif opcion == "3":
            try:
                instruccion = input("\nEscribe la nueva instrucción para el agente: ").strip()
                if instruccion:
                    return False, f"El usuario canceló ese comando y solicitó: '{instruccion}'"
            except (KeyboardInterrupt, EOFError):
                pass
            return False, "Operación cancelada por el usuario."

        elif opcion == "4":
            print("\n❌ Ejecución cancelada.")
            return False, "El usuario canceló la ejecución del comando."
        else:
            print("\n⚠️ Opción no válida. Por favor escribe 1, 2, 3 o 4.")

def extraer_comando_y_contexto(texto: str) -> tuple[str | None, str]:
    """Extrae el comando CMD: y el contexto previo de palabras que dio el agente."""
    match = re.search(r"CMD:\s*([^\n\r]+)", texto)
    if match:
        cmd = match.group(1).strip().strip("`").strip()
        contexto = texto[:match.start()].strip()
        return cmd, contexto

    # Soporte para bloques ```bash o ```sh
    match_code = re.search(r"```(?:bash|sh)?\s*([^\n]+)\s*```", texto)
    if match_code:
        cmd = match_code.group(1).strip()
        contexto = texto[:match_code.start()].strip()
        return cmd, contexto

    return None, texto.strip()

async def obtener_modelos_disponibles(client: httpx.AsyncClient) -> list[str]:
    """Consulta la API de Ollama para listar los modelos descargados."""
    try:
        resp = await client.get(OLLAMA_TAGS_URL, timeout=5.0)
        if resp.status_code == 200:
            datos = resp.json()
            return [m["name"] for m in datos.get("models", [])]
    except Exception:
        pass
    return ["qwen2.5-coder:1.5b", "llama3.2:latest", "phi4-mini:latest"]

async def cambiar_modelo_interactivo(client: httpx.AsyncClient, modelo_actual: str) -> str:
    """Muestra la lista de modelos locales y permite al usuario elegir uno."""
    modelos = await obtener_modelos_disponibles(client)
    print("\n" + "=" * 58)
    print("🧠 \033[1;36mModelos disponibles en Ollama:\033[0m")
    print("=" * 58)
    for idx, m in enumerate(modelos, 1):
        actual_mark = " \033[1;32m(ACTIVO)\033[0m" if m == modelo_actual or m == f"{modelo_actual}:latest" else ""
        print(f" [{idx}] {m}{actual_mark}")
    print("-" * 58)
    print(f"Elige un número [1-{len(modelos)}] o escribe el nombre del modelo:")

    try:
        seleccion = input("Selección: ").strip()
        if not seleccion:
            print("Se mantiene el modelo actual.")
            return modelo_actual
        if seleccion.isdigit():
            num = int(seleccion)
            if 1 <= num <= len(modelos):
                nuevo = modelos[num - 1]
                print(f"\n✔ Modelo cambiado a: \033[1;32m{nuevo}\033[0m\n")
                return nuevo
            else:
                print("Número fuera de rango.")
        else:
            coincidencias = [m for m in modelos if seleccion.lower() in m.lower()]
            if coincidencias:
                nuevo = coincidencias[0]
                print(f"\n✔ Modelo cambiado a: \033[1;32m{nuevo}\033[0m\n")
                return nuevo
            else:
                print(f"No se encontró un modelo que coincida con '{seleccion}'.")
    except (KeyboardInterrupt, EOFError):
        print("\nCambio de modelo cancelado.")

    return modelo_actual

MAX_OUTPUT_LINES = 25  # Truncar salidas largas de comandos para no saturar la CPU
MAX_TURNS_HISTORY = 4  # Mantener solo los últimos turnos en la ventana deslizante

def podar_historial(history: list) -> list:
    """Mantiene el SYSTEM_PROMPT intacto y aplica una ventana deslizante de memoria ligera."""
    if len(history) <= 1:
        return history
    system_msg = history[0]
    conversaciones = history[1:]
    # Cada turno de usuario suele tener entre 1 y 3 mensajes (pregunta, comando, salida, respuesta)
    # Conservamos únicamente los mensajes más recientes
    limite = MAX_TURNS_HISTORY * 3
    if len(conversaciones) > limite:
        conversaciones = conversaciones[-limite:]
    return [system_msg] + conversaciones

def compactar_salida_comando(salida: str, max_lineas: int = MAX_OUTPUT_LINES) -> str:
    """Compacta salidas de comandos extensas para que la CPU de Ollama responda al instante."""
    lineas = salida.strip().splitlines()
    if len(lineas) <= max_lineas:
        return salida.strip()
    primeras = lineas[:max_lineas]
    omitidas = len(lineas) - max_lineas
    return "\n".join(primeras) + f"\n... [Se omitieron {omitidas} líneas para mantener máxima velocidad en CPU] ..."

async def consultar_ia(client: httpx.AsyncClient, model_name: str, messages: list) -> str:
    """Envía la solicitud de chat a Ollama en modo streaming y acumula la respuesta."""
    mensajes_ligeros = podar_historial(messages)
    payload = {
        "model": model_name,
        "messages": mensajes_ligeros,
        "stream": True,
        "options": {
            "temperature": 0.1,
            "num_predict": 512
        }
    }
    req = client.build_request("POST", f"{BASE_URL}/chat/completions", json=payload, timeout=60.0)
    resp = await client.send(req, stream=True)

    texto_acumulado = ""
    async for line in resp.aiter_lines():
        if not line.startswith("data: "):
            continue
        data_str = line[6:].strip()
        if data_str == "[DONE]":
            break
        try:
            chunk = json.loads(data_str)
            delta = chunk["choices"][0].get("delta", {}).get("content", "")
            if delta:
                texto_acumulado += delta
        except json.JSONDecodeError:
            continue

    await resp.aclose()
    return texto_acumulado

async def procesar_turno(client: httpx.AsyncClient, model_name: str, history: list, user_msg: str, stream_output: bool = True):
    """Procesa el turno de usuario, ejecuta comandos si se solicitan y retroalimenta al agente."""
    history.append({"role": "user", "content": user_msg})

    spinner = Spinner(message=f"[{model_name}] pensando...")
    spinner.start()

    try:
        texto_completo = await consultar_ia(client, model_name, history)
    finally:
        await spinner.stop()

    cmd_detectado, contexto = extraer_comando_y_contexto(texto_completo)

    if cmd_detectado:
        if contexto:
            print(f"\nAgente > {contexto}")

        ejecutado, salida = pedir_confirmacion_comando(cmd_detectado)

        spinner = Spinner(message="Analizando resultados...")
        spinner.start()

        history.append({"role": "assistant", "content": f"{contexto}\nCMD: {cmd_detectado}".strip()})
        salida_optimizada = compactar_salida_comando(salida)
        history.append({
            "role": "user",
            "content": (
                f"Resultado de la ejecución del comando `{cmd_detectado}`:\n```\n{salida_optimizada}\n```\n\n"
                "Instrucción para responder:\n"
                "1. Si el comando dio error o no devolvió datos, indícaselo claramente al usuario y sugiere una alternativa.\n"
                "2. Explica y desglosa en español los datos reales obtenidos con detalle técnico, contexto y claridad (temperaturas, componentes, valores principales, etc.).\n"
                "3. No te limites a una frase corta: ofrece un análisis completo, legible y estructurado basado en la salida real."
            )
        })

        try:
            respuesta_final = await consultar_ia(client, model_name, history)
        finally:
            await spinner.stop()

        print(f"\nAgente > {respuesta_final.strip()}\n")
        history.append({"role": "assistant", "content": respuesta_final.strip()})
    else:
        print(f"\nAgente > {texto_completo.strip()}\n")
        history.append({"role": "assistant", "content": texto_completo.strip()})

async def main():
    setup_readline()

    # Soporte para entrada directa por argumentos: agente "pregunta"
    args = sys.argv[1:]
    model_name = DEFAULT_MODEL

    # Si el primer argumento es un modelo conocido o empieza por bandera
    if args and not args[0].startswith("-") and not sys.stdin.isatty():
        pass
    elif args and not args[0].startswith("-") and ":" in args[0]:
        model_name = args.pop(0)

    # Detección de entrada por tubería (pipe): cat archivo | agente "analiza"
    pipe_input = ""
    if not sys.stdin.isatty():
        pipe_input = sys.stdin.read().strip()

    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    async with httpx.AsyncClient() as client:
        # Caso 1: Se pasó consulta directa o por pipe y no es modo interactivo
        if pipe_input or (args and not sys.stdin.isatty()):
            consulta = " ".join(args).strip()
            mensaje_total = f"Contexto/Código recibido por pipe:\n```\n{pipe_input}\n```\n\nPetición: {consulta}" if pipe_input else consulta
            await procesar_turno(client, model_name, history, mensaje_total)
            return

        # Caso 2: Modo interactivo completo
        print("=" * 60)
        print("🤖 \033[1;36mAgente Inteligente Local con Ollama\033[0m")
        print("=" * 60)
        print(f"• Endpoint   : {BASE_URL}")
        print(f"• Modelo     : \033[1;32m{model_name}\033[0m")
        print("• SO         : Linux (Ubuntu)")
        print("• Navegación : Historial con flechas ↑ / ↓")
        print("• Comandos   : '/modelos', '/limpiar', '/ayuda', 'salir'")
        print("=" * 60 + "\n")

        # Si se pasó una pregunta inicial por argumento al abrir la sesión interactiva
        if args:
            pregunta_inicial = " ".join(args).strip()
            print(f"Tú > {pregunta_inicial}")
            await procesar_turno(client, model_name, history, pregunta_inicial)

        while True:
            try:
                user_msg = input("Tú > ").strip()
                if not user_msg:
                    continue

                if user_msg.lower() in ("salir", "exit", "quit", "q"):
                    print("¡Hasta luego!")
                    break

                if user_msg.lower() in ("/limpiar", "/clear", "limpiar"):
                    history = [{"role": "system", "content": SYSTEM_PROMPT}]
                    print("\n🧹 \033[1;32mContexto de la conversación reiniciado.\033[0m\n")
                    continue

                if user_msg.lower() in ("/ayuda", "/help", "ayuda"):
                    print("\n📖 \033[1;36mComandos rápidos disponibles:\033[0m")
                    print("  /modelos          - Muestra y permite cambiar el modelo en caliente")
                    print("  /modelo <nombre>  - Cambia directamente de modelo")
                    print("  /limpiar          - Limpia el historial para liberar memoria")
                    print("  Flechas ↑ / ↓     - Navega por el historial de tus preguntas")
                    print("  salir             - Cierra la sesión\n")
                    continue

                if user_msg.lower() in ("/modelos", "/modelo", "modelos", "cambiar modelo"):
                    model_name = await cambiar_modelo_interactivo(client, model_name)
                    continue

                if user_msg.lower().startswith("/modelo "):
                    partes = user_msg.split(maxsplit=1)
                    if len(partes) > 1:
                        solicitado = partes[1].strip()
                        modelos = await obtener_modelos_disponibles(client)
                        coincidencias = [m for m in modelos if solicitado.lower() in m.lower()]
                        if coincidencias:
                            model_name = coincidencias[0]
                        else:
                            model_name = solicitado
                        print(f"\n✔ Modelo fijado a: \033[1;32m{model_name}\033[0m\n")
                    continue

                await procesar_turno(client, model_name, history, user_msg)

            except (KeyboardInterrupt, EOFError):
                print("\n\nSesión terminada. ¡Hasta luego!")
                break
            except Exception as e:
                print(f"\n❌ Error inesperado: {e}\n")
            finally:
                save_readline()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
