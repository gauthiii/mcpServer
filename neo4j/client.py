import os
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

from langchain_mcp_adapters.client import MultiServerMCPClient
import tool_def_maker


# ------------------------------------------------------------------
# Read MCP config dynamically from neo4j_config.json
# ------------------------------------------------------------------
def load_mcp_config(config_path: str = "neo4j_config.json"):
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

    if tools:
        tool_defs = [tool_def_maker.lc_tool_to_openai_def(t) for t in tools]
        tool_mapping = tool_def_maker.build_tool_mapping(tools, tool_defs)

    import task_executor
    from prompts.create import prompt as p1
    from prompts.relationship import prompt as p2
    from prompts.run import prompt as p3
    from prompts.run import prompt1 as p4
    from prompts.run import prompt2 as p5
    from prompts.run import prompt3 as p6



    res = await task_executor.task_executor_openai(p4, tool_mapping, tool_defs)

    print(res)

    

    




    


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())


