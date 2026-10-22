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

DEFAULT_MODEL = "enoc-agent:latest"
BASE_URL = "http://localhost:11434/v1"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
HISTORIAL_PATH = os.path.expanduser("~/.config/antigravity_agente_history")

SYSTEM_PROMPT = """Eres el asistente del sistema Linux (Ubuntu) de Enoc.
Operas como AGENTE AUTÓNOMO con ejecución real de comandos bash.

REGLAS OBLIGATORIAS:
1. El sistema es LINUX (Ubuntu). NUNCA inventes cifras de RAM, CPU, disco o red sin ejecutar un comando real.
2. Formato estricto para ejecutar comandos bash:
Frase de contexto (1 a 4 palabras).
CMD: <comando bash>
3. MODO AGENTE: Si requieres varios datos, emite UN solo CMD: por turno. Cuando tengas toda la información necesaria, da tu respuesta final limpia en español SIN ningún CMD:.
4. RESPUESTA FINAL OBLIGATORIA:
- NUNCA respondas con frases vacías como "Tu sistema está funcionando correctamente" sin dar cifras.
- Desglosa SIEMPRE las métricas y números reales:
  * Memoria RAM: cita total, en uso y libre/disponible en GB.
  * Almacenamiento: cita total, usado, libre en GB y porcentaje %.
  * Kernel: cita la versión real obtenida.
  * CPU: cita la carga promedio y tiempo activo.
5. PREGUNTAS DE SEGUIMIENTO (ANTI-ALUCINACIÓN):
- Si el usuario hace una pregunta de seguimiento ("y en los otros discos?", "y el disco externo?", "y de ram?", "y de swap?"):
  NUNCA repitas los datos anteriores ni inventes cifras. Ejecuta SIEMPRE el comando real correspondiente (CMD: lsblk, CMD: free -h, CMD: df -h, etc.).

RECETAS ESENCIALES:
- Kernel y versión del SO: CMD: uname -r
- Distribución de Linux: CMD: lsb_release -d 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME
- Memoria RAM y Swap: CMD: free -h
- Disco principal: CMD: df -h /
- Todos los discos, particiones y discos externos: CMD: lsblk -e7 -o NAME,SIZE,FSTYPE,TYPE,MOUNTPOINTS
- Carga de CPU y actividad: CMD: uptime
- Temperatura y ventiladores: CMD: sensors
- Procesos pesados: CMD: ps aux --sort=-%mem | head -n 8
- Red e IP privada: CMD: ip -br addr
- Puerta de enlace: CMD: ip route show default
- IP pública: CMD: curl -s https://ifconfig.me
- Buscar, filtrar y explorar comandos del sistema:
  * Buscar comandos por tema o función: CMD: apropos <tema>
  * Para qué sirve un comando (resumen de una línea): CMD: whatis <comando>
  * Ver comandos disponibles en el sistema: CMD: compgen -c | sort -u | head -n 35
  * Filtrar comandos por nombre: CMD: compgen -c | grep <palabra> | sort -u
  * Filtrador difuso de comandos: CMD: fzf
  * Comandos internos de Bash: CMD: help
  * Ubicar ruta de un ejecutable: CMD: which <comando> || whereis <comando>
  * Gestor modular de comandos del usuario: CMD: adm || ~/dev/personal/gestor-comandos-cli/adm
- Batería: CMD: upower -i $(upower -e | grep 'BAT') 2>/dev/null || acpi 2>/dev/null
- Apagar PC: CMD: systemctl poweroff || sudo poweroff
- Reiniciar PC: CMD: systemctl reboot || sudo reboot
"""

# Comandos de alto riesgo para advertencia visual
DANGEROUS_PATTERNS = [
    r"\brm\s+-[rf]*\b",
    r"\bmkfs\b",
    r"\bdd\b",
    r">\s*/dev/sd[a-z]",
    r"\bchmod\s+-R\s+777\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bpoweroff\b",
    r"\bsystemctl\s+(poweroff|reboot)\b",
]

# Comandos seguros (solo lectura / consulta) que se auto-ejecutan sin pedir confirmación manual
SAFE_PATTERNS = [
    r"^df\b",
    r"^free\b",
    r"^uptime\b",
    r"^whoami\b",
    r"^hostname\b",
    r"^uname\b",
    r"^cat\b",
    r"^head\b",
    r"^tail\b",
    r"^wc\b",
    r"^ls\b",
    r"^pwd\b",
    r"^ip\b",
    r"^ifconfig\b",
    r"^ps\b",
    r"^top\b",
    r"^htop\b",
    r"^sensors\b",
    r"^lscpu\b",
    r"^lsblk\b",
    r"^lsusb\b",
    r"^lspci\b",
    r"^which\b",
    r"^type\b",
    r"^whatis\b",
    r"^apropos\b",
    r"^compgen\b",
    r"^whereis\b",
    r"^help\b",
    r"^adm\b",
    r"^fzf\b",
    r"^date\b",
    r"^cal\b",
    r"^id\b",
    r"^groups\b",
    r"^dpkg\s+-l\b",
    r"^dpkg\s+-L\b",
    r"^dpkg\s+-s\b",
    r"^apt\s+list\b",
    r"^apt\s+show\b",
    r"^apt\s+search\b",
    r"^pip3?\s+list\b",
    r"^pip3?\s+show\b",
    r"^npm\s+list\b",
    r"^npm\s+ls\b",
    r"^git\s+(status|log|branch|diff|show|remote)\b",
    r"^docker\s+(ps|images|logs|inspect)\b",
    r"^find\b",
    r"^grep\b",
    r"^wc\b",
    r"^du\b",
    r"^curl\s+-s\b",
    r"^wget\s+-q\b",
    r"^upower\b",
    r"^acpi\b",
    r"^man\b",
    r"^python3?\s+--version\b",
    r"^node\s+--version\b",
    r"^ollama\s+(list|ps|show)\b",
    r"^systemctl\s+status\b",
    r"^wpctl\s+status\b",
    r"^lsb_release\b",
]

MAX_AGENT_STEPS = 4  # Máximo de comandos encadenados por turno de usuario

SPINNER_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class Spinner:
    def __init__(self, message: str = "Pensando..."):
        self.message = message
        self.running = False
        self.task = None

    async def _spin(self):
        if not sys.stdout.isatty():
            return
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
    except OSError:
        pass


def save_readline():
    """Guarda el historial de comandos al cerrar la sesión."""
    try:
        readline.write_history_file(HISTORIAL_PATH)
    except OSError:
        pass


def es_comando_peligroso(cmd: str) -> bool:
    """Verifica si el comando contiene patrones potencialmente destructivos."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd):
            return True
    return False


def es_comando_seguro(cmd: str) -> bool:
    """Verifica si el comando es de solo lectura/consulta y puede auto-ejecutarse."""
    # Si contiene cualquier patrón peligroso en cualquier parte, nunca es seguro
    if es_comando_peligroso(cmd):
        return False
    # Verificar que cada comando encadenado (por && o ;) sea seguro
    sub_comandos = re.split(r"\s*(?:&&|;)\s*", cmd.strip())
    for sub in sub_comandos:
        primer_cmd = sub.split("|")[0].strip()
        if not any(re.search(pattern, primer_cmd) for pattern in SAFE_PATTERNS):
            return False
    return True


def ejecutar_comando_directo(cmd: str, timeout: int = 25) -> tuple[bool, str]:
    """Ejecuta un comando directamente sin pedir confirmación (para comandos seguros)."""
    try:
        res = subprocess.run(
            cmd, check=False, shell=True, capture_output=True, text=True, timeout=timeout
        )
        salida = res.stdout if res.returncode == 0 else (res.stderr or res.stdout)
        return True, salida.strip() or "(Comando ejecutado con éxito sin salida)"
    except subprocess.TimeoutExpired:
        return False, "Error: El comando tardó demasiado tiempo y fue cancelado."
    except (subprocess.SubprocessError, OSError) as e:
        return False, f"Error al ejecutar: {e}"


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
                    check=False,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=25,
                )
                salida = (
                    res.stdout if res.returncode == 0 else (res.stderr or res.stdout)
                )
                return (
                    True,
                    salida.strip() or "(Comando ejecutado con éxito sin salida)",
                )
            except subprocess.TimeoutExpired:
                return (
                    False,
                    "Error: El comando tardó demasiado tiempo y fue cancelado.",
                )
            except (subprocess.SubprocessError, OSError) as e:
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
                instruccion = input(
                    "\nEscribe la nueva instrucción para el agente: "
                ).strip()
                if instruccion:
                    return (
                        False,
                        f"El usuario canceló ese comando y solicitó: '{instruccion}'",
                    )
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
        contexto = texto[: match.start()].strip()
        return cmd, contexto

    # Solo buscar bloque ```bash si la respuesta entera es exclusivamente el bloque de código
    # (evita falsos positivos en bucle cuando el agente da ejemplos o explicaciones en texto)
    match_code = re.match(r"^\s*```(?:bash|sh)?\s*\n?([^\n]+)\s*```\s*$", texto.strip())
    if match_code:
        cmd = match_code.group(1).strip()
        return cmd, ""

    return None, texto.strip()


async def obtener_modelos_disponibles(client: httpx.AsyncClient) -> list[str]:
    """Consulta la API de Ollama para listar los modelos descargados."""
    try:
        resp = await client.get(OLLAMA_TAGS_URL, timeout=5.0)
        if resp.status_code == 200:
            datos = resp.json()
            return [m["name"] for m in datos.get("models", [])]
    except (httpx.HTTPError, json.JSONDecodeError, KeyError):
        pass
    return ["qwen2.5-coder:1.5b", "llama3.2:latest", "phi4-mini:latest"]


async def cambiar_modelo_interactivo(
    client: httpx.AsyncClient, modelo_actual: str
) -> str:
    """Muestra la lista de modelos locales y permite al usuario elegir uno."""
    modelos = await obtener_modelos_disponibles(client)
    print("\n" + "=" * 58)
    print("🧠 \033[1;36mModelos disponibles en Ollama:\033[0m")
    print("=" * 58)
    for idx, m in enumerate(modelos, 1):
        actual_mark = (
            " \033[1;32m(ACTIVO)\033[0m"
            if m == modelo_actual or m == f"{modelo_actual}:latest"
            else ""
        )
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


# Parámetros optimizados para bajo consumo de recursos (CPU / RAM baja / 2 a 4 núcleos)
CPU_COUNT = os.cpu_count() or 2
OPTIMAL_THREADS = max(1, min(4, CPU_COUNT - 1))
MAX_OUTPUT_LINES = 16  # Truncar salidas largas de comandos para no saturar la CPU
MAX_TURNS_HISTORY = 4  # Ventana deslizante ligera (4 turnos) óptima para PCs de bajos recursos


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
    return (
        "\n".join(primeras)
        + f"\n... [Se omitieron {omitidas} líneas para mantener máxima velocidad en CPU] ..."
    )


async def consultar_ia(
    client: httpx.AsyncClient, model_name: str, messages: list
) -> str:
    """Envía la solicitud de chat a Ollama en modo streaming y acumula la respuesta."""
    mensajes_ligeros = podar_historial(messages)
    payload = {
        "model": model_name,
        "messages": mensajes_ligeros,
        "stream": True,
        "temperature": 0.0,
        "max_tokens": 192,
        "options": {
            "temperature": 0.0,
            "num_predict": 192,
            "num_ctx": 2048,
            "num_thread": OPTIMAL_THREADS,
        },
        "keep_alive": "30m",
    }
    req = client.build_request(
        "POST", f"{BASE_URL}/chat/completions", json=payload, timeout=30.0
    )
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


async def procesar_turno(
    client: httpx.AsyncClient,
    model_name: str,
    history: list,
    user_msg: str,
    stream_output: bool = True,
):
    """Procesa el turno de usuario con BUCLE AGENTE: encadena múltiples comandos hasta completar la tarea."""
    history.append({"role": "user", "content": user_msg})

    for step in range(MAX_AGENT_STEPS):
        spinner = Spinner(
            message=f"[{model_name}] {'pensando...' if step == 0 else f'paso {step + 1} — analizando...'}"
        )
        spinner.start()

        try:
            texto_completo = await consultar_ia(client, model_name, history)
        finally:
            await spinner.stop()

        cmd_detectado, contexto = extraer_comando_y_contexto(texto_completo)

        if not cmd_detectado:
            # No hay más comandos → respuesta final del agente
            print(f"\nAgente > {texto_completo.strip()}\n")
            history.append({"role": "assistant", "content": texto_completo.strip()})
            return

        # Mostrar la frase de contexto si la hay
        if contexto:
            print(f"\nAgente > {contexto}")

        # Decidir si auto-ejecutar (seguro) o pedir confirmación
        if es_comando_seguro(cmd_detectado):
            print(
                f"\n🔍 \033[1;34mEjecutando automáticamente:\033[0m \033[1;32m{cmd_detectado}\033[0m"
            )
            ejecutado, salida = ejecutar_comando_directo(cmd_detectado)
        else:
            ejecutado, salida = pedir_confirmacion_comando(cmd_detectado)

        # Registrar en el historial lo que hizo el agente
        history.append(
            {
                "role": "assistant",
                "content": f"{contexto}\nCMD: {cmd_detectado}".strip(),
            }
        )
        salida_optimizada = compactar_salida_comando(salida)

        if not ejecutado and "canceló" in salida.lower():
            # El usuario canceló → no seguir encadenando
            history.append(
                {
                    "role": "user",
                    "content": f"El usuario canceló la ejecución de '{cmd_detectado}'.",
                }
            )
            print("\nAgente > Entendido, comando cancelado.\n")
            history.append(
                {"role": "assistant", "content": "Entendido, comando cancelado."}
            )
            return

        # Retroalimentar al agente con la salida del comando
        es_ultimo_paso = step == MAX_AGENT_STEPS - 1
        if es_ultimo_paso:
            instruccion = (
                "Último paso. Responde al usuario desglosando las cifras reales (memoria RAM total/usada/libre, disco, carga, etc.). "
                "PROHIBIDO responder solo 'el sistema funciona correctamente'. Da un resumen claro con viñetas y datos exactos. NO emitas más CMD:."
            )
        else:
            instruccion = (
                "Si la consulta requiere revisar más componentes (como disco df -h / o carga uptime), emite el siguiente CMD: con su frase corta.\n"
                "Si ya tienes los datos para responder la consulta del usuario, desglosa las cifras reales obtenidas (total, usado, libre, etc.). "
                "PROHIBIDO responder solo 'funciona correctamente'. NO emitas más CMD: si ya vas a responder."
            )

        history.append(
            {
                "role": "user",
                "content": (
                    f"Resultado de `{cmd_detectado}`:\n```\n{salida_optimizada}\n```\n\n"
                    f"{instruccion}"
                ),
            }
        )

    # Si se agotaron los pasos, pedir respuesta final forzada
    spinner = Spinner(message="Generando resumen final...")
    spinner.start()
    try:
        respuesta_final = await consultar_ia(client, model_name, history)
    finally:
        await spinner.stop()
    # Limpiar cualquier CMD residual de la respuesta final
    respuesta_limpia = re.sub(r"CMD:\s*[^\n\r]+", "", respuesta_final).strip()
    print(f"\nAgente > {respuesta_limpia}\n")
    history.append({"role": "assistant", "content": respuesta_limpia})


async def main():
    setup_readline()

    # Soporte para entrada directa por argumentos: agente "pregunta"
    args = sys.argv[1:]
    model_name = DEFAULT_MODEL

    # Si el primer argumento es un modelo conocido (ej: modelo:tag)
    if args and not args[0].startswith("-") and ":" in args[0]:
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
            mensaje_total = (
                f"Contexto/Código recibido por pipe:\n```\n{pipe_input}\n```\n\nPetición: {consulta}"
                if pipe_input
                else consulta
            )
            await procesar_turno(client, model_name, history, mensaje_total)
            return

        # Caso 2: Modo interactivo completo
        print("=" * 60)
        print("🤖 \033[1;36mAgente Inteligente Local con Ollama\033[0m")
        print("=" * 60)
        print(f"• Endpoint   : {BASE_URL}")
        print(f"• Modelo     : \033[1;32m{model_name}\033[0m")
        print(f"• Hardware   : {CPU_COUNT} CPUs detectados ({OPTIMAL_THREADS} hilos optimizados para baja latencia)")
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
                    print(
                        "\n🧹 \033[1;32mContexto de la conversación reiniciado.\033[0m\n"
                    )
                    continue

                if user_msg.lower() in ("/ayuda", "/help", "ayuda"):
                    print("\n📖 \033[1;36mComandos rápidos disponibles:\033[0m")
                    print(
                        "  /modelos          - Muestra y permite cambiar el modelo en caliente"
                    )
                    print("  /modelo <nombre>  - Cambia directamente de modelo")
                    print(
                        "  /limpiar          - Limpia el historial para liberar memoria"
                    )
                    print(
                        "  Flechas ↑ / ↓     - Navega por el historial de tus preguntas"
                    )
                    print("  salir             - Cierra la sesión\n")
                    continue

                if user_msg.lower() in (
                    "/modelos",
                    "/modelo",
                    "modelos",
                    "cambiar modelo",
                ):
                    model_name = await cambiar_modelo_interactivo(client, model_name)
                    continue

                if user_msg.lower().startswith("/modelo "):
                    partes = user_msg.split(maxsplit=1)
                    if len(partes) > 1:
                        solicitado = partes[1].strip()
                        modelos = await obtener_modelos_disponibles(client)
                        coincidencias = [
                            m for m in modelos if solicitado.lower() in m.lower()
                        ]
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
            except Exception as e:  # noqa: BLE001
                print(f"\n❌ Error inesperado: {e}\n")
            finally:
                save_readline()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
