# neo4j_runner.py

import os
import json
from typing import Dict, Any, List

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
import tool_def_maker
import task_executor  # your existing module

load_dotenv()

MCP_CONFIG_PATH = "neo4j_config.json"

def load_mcp_config(config_path: str = MCP_CONFIG_PATH):
    with open(config_path, "r") as f:
        cfg = json.load(f)
    return cfg.get("mcpServers", {})


async def run_neo4j_task(user_prompt: str) -> str:
    """
    This is basically your `main()` from client.py,
    but parameterized by a prompt coming from the UI.
    """

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

    # 5️⃣ Collect prompts exposed by the MCP servers (schema as system prompt)
    systemPromptMessage = await client.get_prompt(
        server_name="neo4j",
        prompt_name="neo4j_schema"
    )

    # convert first MCP prompt message to a proper system message
    first = systemPromptMessage[0]
    content = getattr(first, "content", "") if not isinstance(first, dict) else first.get("content", "")
    systemPrompt = {"role": "system", "content": content or "Schema prompt contained no content."}

    if not tools:
        raise RuntimeError("No MCP tools discovered. Check your MCP server.")

    tool_defs = [tool_def_maker.lc_tool_to_openai_def(t) for t in tools]
    tool_mapping = tool_def_maker.build_tool_mapping(tools, tool_defs)

    # 🔥 Instead of importing promptx, we use `user_prompt` from UI
    res = await task_executor.task_executor_openai(
        strategy=user_prompt,
        tool_mapping=tool_mapping,
        tool_defs=tool_defs,
        systemPrompt=systemPrompt,
    )

    return res
