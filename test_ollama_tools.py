import asyncio
from google.antigravity import Agent, LocalOpenAIAgentConfig

def get_system_status() -> str:
    """Returns the current operational status of the local workstation."""
    return "Todos los sistemas locales y Ollama operando con fluidez normal."

async def main():
    config = LocalOpenAIAgentConfig(
        base_url="http://localhost:11434/v1",
        model="llama3.2:latest",
        tools=[get_system_status],
    ).lightweight()

    print("--- Probando Antigravity con Ollama y herramientas ---")
    async with Agent(config) as agent:
        response = await agent.chat("Verifica el estado del sistema con la herramienta disponible y dame un reporte breve en español.")
        print("\nResultado:")
        print(await response.text())

if __name__ == "__main__":
    asyncio.run(main())
