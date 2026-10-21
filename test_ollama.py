import asyncio
from google.antigravity import Agent, LocalOpenAIAgentConfig

async def main():
    config = LocalOpenAIAgentConfig(
        base_url="http://localhost:11434/v1",
        model="llama3.2:latest",
    ).lightweight()

    print("Iniciando agente con Ollama (llama3.2:latest)...")
    async with Agent(config) as agent:
        response = await agent.chat("Hola, responde en una frase quién eres.")
        print("Respuesta recibida:")
        print(await response.text())

if __name__ == "__main__":
    asyncio.run(main())
