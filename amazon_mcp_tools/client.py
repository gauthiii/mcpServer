import os
import json
import asyncio
from dotenv import load_dotenv
import agents.planner, agents.task_executor, agents.reflector, agents.final_eval


# MCP + LangChain imports
from langchain_mcp_adapters.client import MultiServerMCPClient
import tool_def_maker

# Load environment variables
load_dotenv()

# https://github.com/r123singh/amazon-mcp-server


# ------------------------------------------------------------------
# Read MCP config dynamically from config.json
# ------------------------------------------------------------------
def load_mcp_config(config_path: str = "config.json"):
    with open(config_path, "r") as f:
        cfg = json.load(f)
    return cfg.get("mcpServers", {})

# ------------------------------------------------------------------
# AGENTS
# ------------------------------------------------------------------

# groq:llama-3.1-8b-instant
# openai:gpt-4o-mini
# anthropic:claude-haiku-4-5
# ollama:gemma3:latest

# MIGRATED TO THE AGENTS FOLDER

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

    
    strategy= agents.planner.planner_ollama("Find the best phone under $1000.",tool_defs)
    print(strategy)
    print("*************************")

    answer = await agents.task_executor.task_executor_ollama(strategy,tool_mapping,tool_defs)
    print(answer)
    print("*************************")

    # # import time

    # # time.sleep(30)

    reflection = await agents.reflector.reflector_ollama(strategy, answer,tool_mapping,tool_defs)
    print(reflection)
    print("*************************")



    eval = await agents.final_eval.final_eval_ollama(reflection,tool_mapping,tool_defs)
    print(eval)
    print("*************************")


    
    # x= await agents.compare_products.compare_products_groq(tool_mapping,tool_defs)
    # print(x)



# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())
