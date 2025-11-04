import os
import json
import asyncio
from dotenv import load_dotenv

# MCP + LangChain imports
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI  # <— for OpenAI models

# Load environment variables
load_dotenv()

# Also another available at https://github.com/PaulFidika/gmail-mcp-server

# ------------------------------------------------------------------
# Read MCP config dynamically from config.json
# ------------------------------------------------------------------
def load_mcp_config(config_path: str = "config.json"):
    with open(config_path, "r") as f:
        cfg = json.load(f)
    return cfg.get("mcpServers", {})

# ------------------------------------------------------------------
# Main async routine
# ------------------------------------------------------------------
async def main():
    # 1️⃣ Load MCP servers from config.json
    mcp_servers = load_mcp_config()

    # 2️⃣ Initialize MCP client
    client = MultiServerMCPClient(mcp_servers)

    # 3️⃣ Ensure OpenAI key is available
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("❌ OPENAI_API_KEY not found in .env file!")

    # 4️⃣ Collect tools exposed by the MCP servers
    tools = await client.get_tools()

    # 5️⃣ Initialize the model (you can use gpt-4o-mini or gpt-3.5-turbo)
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    # 6️⃣ Create the ReAct agent
    agent = create_react_agent(model, tools)

    # 7️⃣ Test a query that uses any of your MCP tools
    test_query = "Check if my Gmail account is connected and list the subject of the 3 most recent emails."

    print(f"🧠 Running query: {test_query}\n{'-'*70}")
    response = await agent.ainvoke({"messages": [{"role": "user", "content": test_query}]})

    print("\n✅ Final Response:")
    print(response["messages"][-1].content)
    print("\n⭐ Done!")

# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())
