import asyncio
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient

async def main():
    # Load environment variables (expects GROQ_API_KEY in your .env)
    load_dotenv()

    # Create configuration dictionary
    config = {
        "mcpServers": {
            "playwright": {
                "command": "npx",
                "args": ["@playwright/mcp@latest"],
                "env": {
                    "DISPLAY": ":1"
                }
            }
        }
    }

    # Create MCPClient from configuration dictionary
    # client = MCPClient.from_dict(config)

    # Or: Create MCPClient from config json file.
    client = MCPClient.from_config_file(
        os.path.join("browser_mcp.json")
    )

    # Create LLM (Groq)
    llm = ChatGroq(
        model="qwen/qwen3-32b",
        temperature=0.2,
        max_retries=2,
    )

    # Create agent with the client
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    # Run the query
    result = await agent.run("Find the best restaurant in Tempe")
    print(f"\nResult: {result}")

if __name__ == "__main__":
    asyncio.run(main())
