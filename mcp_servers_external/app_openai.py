import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient

async def main():
    # Load environment variables (expects OPENAI_API_KEY in your .env)
    load_dotenv("../.env")

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

    # Create LLM (OpenAI)
    llm = ChatOpenAI(
        model="gpt-4o-mini",  # or "gpt-4-turbo", "gpt-4o"
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
