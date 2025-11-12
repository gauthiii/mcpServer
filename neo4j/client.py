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

    # print(tool_defs)

    # print(json.dumps(tool_defs,indent=4))

    prompt = f'''

Create the following node with the following label and properties

- Label: Movies
- Properties:
    - name: Thuppakki

- Label: Movies
- Properties:
    - name: Vikram

- Label: Movies
- Properties:
    - name: Leo

- Label: Movies
- Properties:
    - name: Jailer


Once you have created nodes, I need to see all the nodes under Movies label

Along with the strategy give me the query you will use to see all the nodes.


'''
    
    prompt = f'''

    Create a relationship for the following.

    Tom from label Cartoon likes watching Thuppakki from label Movies.
    Jerry from label Cartoon like watching Leo from label Movies.



'''
    

    # strategy = task_executor.planner_ollama(prompt, tool_defs)

    # print(strategy)

    # res = await task_executor.task_executor_openai(strategy,tool_mapping, tool_defs)

    res = await task_executor.task_executor_openai("Give me the entire schema view", tool_mapping, tool_defs)

    print(res)

    

    




    


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())


