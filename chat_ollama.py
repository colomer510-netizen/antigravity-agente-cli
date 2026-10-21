#!/usr/bin/env python3
"""
Agente Inteligente Ultra-Rápido con Ollama y Control del Sistema Linux.
- Conexión directa streaming a través de Ollama.
- Mensaje breve de contexto antes de solicitar el comando.
- Menú interactivo de seguridad: [1-4]
- Inyección obligatoria de SYSTEM_PROMPT de Linux para cualquier modelo.
- Soporte para cambio dinámico de modelos en caliente (/modelos o /modelo [nombre])
"""

import asyncio
import itertools
import json
import re
import subprocess
import sys
import httpx

DEFAULT_MODEL = "qwen2.5-coder:1.5b"
BASE_URL = "http://localhost:11434/v1"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

SYSTEM_PROMPT = """Eres el asistente del sistema Linux (Ubuntu) de Enoc.
Tu misión principal es monitorear y gestionar el sistema operativo Linux con precisión técnica real.

REGLAS ABSOLUTAS:
1. El sistema operativo es LINUX (Ubuntu), NUNCA Windows ni macOS. Jamás uses comandos de Windows (como dir, cls, tasklist, etc.).
2. NUNCA inventes números ni estados de RAM, disco, CPU o red sin ejecutar un comando real.
3. Para ejecutar un comando bash en Linux, debes responder SIEMPRE en este formato exacto:
Una frase corta de contexto (1 a 4 palabras).
CMD: <comando bash>

Ejemplos de comandos obligatorios en Linux:
- Almacenamiento / Disco: CMD: df -h /
- Memoria RAM: CMD: free -h
- Procesos que consumen RAM: CMD: ps aux --sort=-%mem | head -n 8
- Procesos que consumen CPU: CMD: ps aux --sort=-%cpu | head -n 8
- Estado o carga de CPU: CMD: uptime
- Dirección IP / Red: CMD: hostname -I
- Información de hardware / batería: CMD: upower -i $(upower -e | grep 'BAT') 2>/dev/null || acpi 2>/dev/null
"""

# Animación de carga estilo Ollama (braille / puntos)
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
                await self.task

def pedir_confirmacion_comando(cmd_propuesto: str) -> tuple[bool, str]:
    """Muestra el menú interactivo para aprobar, editar o cancelar un comando."""
    cmd_actual = cmd_propuesto
    while True:
        print("\n" + "=" * 55)
        print("⚙️  \033[1;33mEl Agente solicita ejecutar un comando en Linux:\033[0m")
        print(f"   \033[1;32m{cmd_actual}\033[0m")
        print("=" * 55)
        print("¿Qué deseas hacer?")
        print(" [1] Sí, ejecutar comando")
        print(" [2] Modificar comando manualmente")
        print(" [3] Dar otras instrucciones / feedback al agente")
        print(" [4] Cancelar")
        print("-" * 55)

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
                    timeout=20
                )
                salida = res.stdout if res.returncode == 0 else res.stderr
                return True, salida.strip() or "(Comando ejecutado con éxito sin salida)"
            except subprocess.TimeoutExpired:
                return False, "Error: El comando tardó demasiado tiempo y se canceló."
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
                    return False, f"El usuario no ejecutó el comando y pidió: '{instruccion}'"
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
    
    # Soporte para bloques bash
    match_code = re.search(r"```(?:bash|sh)?\s*([^\n]+)\s*```", texto)
    if match_code:
        cmd = match_code.group(1).strip()
        contexto = texto[:match_code.start()].strip()
        return cmd, contexto

    return None, texto.strip()

async def obtener_modelos_disponibles(client: httpx.AsyncClient) -> list[str]:
    """Consulta la API nativa de Ollama para listar los modelos descargados."""
    try:
        resp = await client.get(OLLAMA_TAGS_URL, timeout=5.0)
        if resp.status_code == 200:
            datos = resp.json()
            return [m["name"] for m in datos.get("models", [])]
    except Exception:
        pass
    return ["qwen2.5-coder:3b", "enoc-agent:latest", "phi4-mini:latest", "qwen2.5-coder:1.5b"]

async def cambiar_modelo_interactivo(client: httpx.AsyncClient, modelo_actual: str) -> str:
    """Muestra la lista de modelos locales y permite al usuario elegir uno."""
    modelos = await obtener_modelos_disponibles(client)
    print("\n" + "=" * 55)
    print("🧠 \033[1;36mModelos disponibles en Ollama:\033[0m")
    print("=" * 55)
    for idx, m in enumerate(modelos, 1):
        actual_mark = " \033[1;32m(ACTIVO)\033[0m" if m == modelo_actual or m == f"{modelo_actual}:latest" else ""
        print(f" [{idx}] {m}{actual_mark}")
    print("-" * 55)
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

async def main():
    model_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL

    print("=" * 60)
    print("🤖 Agente Inteligente Local con Ollama")
    print("=" * 60)
    print(f"• Endpoint : {BASE_URL}")
    print(f"• Modelo   : \033[1;32m{model_name}\033[0m")
    print("• SO       : Linux (Ubuntu)")
    print("• Control  : Opciones [1-4] antes de ejecutar comandos")
    print("• Comandos : '/modelos' o '/modelo' para cambiar de IA")
    print("• Salir    : 'salir' o Ctrl+C para terminar.\n")

    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    async with httpx.AsyncClient() as client:
        while True:
            try:
                user_msg = input("\nTú > ").strip()
                if not user_msg:
                    continue
                if user_msg.lower() in ("salir", "exit", "quit"):
                    print("¡Hasta luego!")
                    break

                # COMANDO PARA CAMBIAR DE MODELO EN CALIENTE
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
                            print(f"\n✔ Modelo cambiado a: \033[1;32m{model_name}\033[0m")
                        else:
                            model_name = solicitado
                            print(f"\n✔ Modelo fijado a: \033[1;32m{model_name}\033[0m")
                        continue

                history.append({"role": "user", "content": user_msg})

                spinner = Spinner(message=f"[{model_name}] pensando...")
                spinner.start()

                payload = {
                    "model": model_name,
                    "messages": history,
                    "stream": True,
                    "options": {"temperature": 0.0}
                }

                req = client.build_request("POST", f"{BASE_URL}/chat/completions", json=payload, timeout=60.0)
                resp = await client.send(req, stream=True)

                texto_completo = ""

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        chunk_json = json.loads(data_str)
                        delta = chunk_json["choices"][0].get("delta", {}).get("content", "")
                        if delta:
                            texto_completo += delta
                    except json.JSONDecodeError:
                        continue

                await resp.aclose()
                await spinner.stop()

                # Separar comando y mensaje de contexto
                cmd_detectado, contexto = extraer_comando_y_contexto(texto_completo)

                if cmd_detectado:
                    if contexto:
                        print(f"\nAgente > {contexto}")

                    # Mostrar el menú interactivo [1-4]
                    ejecutado, salida = pedir_confirmacion_comando(cmd_detectado)

                    spinner = Spinner(message="Procesando datos...")
                    spinner.start()

                    history.append({"role": "assistant", "content": f"{contexto}\nCMD: {cmd_detectado}".strip()})
                    history.append({
                        "role": "user",
                        "content": f"Salida real del comando ({cmd_detectado}):\n```\n{salida}\n```\n\nInstrucción: Extrae y reporta de forma exacta los números y datos reales de la salida anterior al usuario en español en 1 o 2 líneas claras. NUNCA inventes números que no estén en la salida."
                    })

                    payload_res = {
                        "model": model_name,
                        "messages": history,
                        "stream": True,
                        "options": {"temperature": 0.0}
                    }

                    req2 = client.build_request("POST", f"{BASE_URL}/chat/completions", json=payload_res, timeout=60.0)
                    resp2 = await client.send(req2, stream=True)

                    await spinner.stop()
                    print("\nAgente > ", end="", flush=True)
                    respuesta_final = ""

                    async for line2 in resp2.aiter_lines():
                        if not line2.startswith("data: "):
                            continue
                        data_str2 = line2[6:].strip()
                        if data_str2 == "[DONE]":
                            break
                        try:
                            chunk_json2 = json.loads(data_str2)
                            delta2 = chunk_json2["choices"][0].get("delta", {}).get("content", "")
                            if delta2:
                                respuesta_final += delta2
                                sys.stdout.write(delta2)
                                sys.stdout.flush()
                        except json.JSONDecodeError:
                            continue

                    print()
                    history.append({"role": "assistant", "content": respuesta_final.strip()})

                else:
                    # Conversación normal sin comando
                    print(f"\nAgente > {texto_completo.strip()}")
                    history.append({"role": "assistant", "content": texto_completo.strip()})

            except KeyboardInterrupt:
                print("\n\nSesión terminada. ¡Hasta luego!")
                break
            except Exception as e:
                print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
