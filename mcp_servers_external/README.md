# Project 1: External MCP Servers Integration (`mcp_servers_external`)

## 1. Project Overview

This project demonstrates how to give Large Language Models (LLMs) **real-world capabilities** by connecting them to multiple external **MCP Servers**. Instead of just generating text, the LLM can now browse the live web, search DuckDuckGo, and look up Airbnb listings.

**Goal:** Create a unified agent that can perform complex "real-world" tasks (like "Find the best restaurant in Tempe") by autonomously selecting and controlling the appropriate external tools.

---

## 2. Architecture & Components

The system uses a **Multi-Server Architecture** where a single Python client connects to three distinct Node.js-based MCP servers.

| Component | Technology | Role |
| --- | --- | --- |
| **Browser Tool** | `@playwright/mcp` | Allows the agent to open a browser, navigate to URLs, click buttons, and read page content. |
| **Search Tool** | `duckduckgo-mcp-server` | Provides privacy-focused web search results (snippets and links). |
| **Booking Tool** | `@openbnb/mcp-server-airbnb` | Connects to Airbnb data to find lodging. |
| **Orchestrator** | `mcp_use` / `LangChain` | Managing the conversation history and tool-calling loop. |
| **LLM** | Groq (`qwen3-32b`) / OpenAI (`gpt-4o-mini`) | The "Brain" that decides which tool to use based on the user's prompt. |

---

## 3. Configuration (`browser_mcp.json`)

The core of this project is the JSON configuration file. This tells the MCP Client how to start the external servers. Since these are Node.js packages, we use `npx` to execute them directly.

**`browser_mcp.json`**

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    },
    "airbnb": {
      "command": "npx",
      "args": ["-y", "@openbnb/mcp-server-airbnb"]
    },
    "duckduckgo-search": {
      "command": "npx",
      "args": ["-y", "duckduckgo-mcp-server"]
    }
  }
}

```

---

## 4. Code Breakdown

The project includes two implementations to demonstrate flexibility across different LLM providers.

### Key Logic

Both scripts follow the same pattern:

1. **Load Config:** `MCPClient.from_config_file("browser_mcp.json")` reads the JSON above and spins up the 3 servers in the background.
2. **Initialize LLM:** Connects to either Groq or OpenAI.
3. **Initialize Agent:** `MCPAgent(llm=llm, client=client)` creates a LangChain-based agent that automatically detects the tools exposed by the 3 connected servers.
4. **Execute:** `agent.run(...)` starts the reasoning loop.

### Implementation 1: Groq (Open Source / Fast Inference)

Uses `ChatGroq` with the `qwen/qwen3-32b` model. This demonstrates how to use high-performance open-source models for tool use.

### Implementation 2: OpenAI (GPT-4o)

Uses `ChatOpenAI` with `gpt-4o-mini`. This is generally more robust for complex navigation tasks requiring high reasoning capabilities.

---

## 5. How to Run

### Prerequisites

* **Node.js & npm:** Required to run the `npx` commands for the servers.
* **Python 3.10+ & uv:** For the Python client.
* **API Keys:** Ensure `GROQ_API_KEY` and `OPENAI_API_KEY` are in your `.env`.

### Steps

1. **Create the Config File:** Save the JSON block above as `browser_mcp.json` in your project directory.
2. **Run the Groq Agent:**
```bash
python groq_agent.py

```


3. **Run the OpenAI Agent:**
```bash
python openai_agent.py

```



### Expected Output

When you run the query *"Find the best restaurant in Tempe"*, you will see the agent:

1. **Connect** to the Playwright/DuckDuckGo servers.
2. **Decide** to use the `playwright_navigate` or `duckduckgo_search` tool.
3. **Fetch** results from the web.
4. **Synthesize** a final answer (e.g., "Based on search results, Top of the Rock and House of Tricks are highly rated...").
