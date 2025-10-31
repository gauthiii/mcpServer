# MCP + Groq Playwright Agent

This project demonstrates an **MCP-enabled agent** that uses:
- **Groq** (LLM via `langchain_groq`)
- **Playwright MCP** (browser automation via MCP server)
- Optional extra MCP servers: **Airbnb** and **DuckDuckGo Search**
- A simple agent wrapper (`MCPAgent`, `MCPClient`) to orchestrate tool calls

The agent runs a query like _“Find the best restaurant in Tempe”_ and can browse/automate via MCP.