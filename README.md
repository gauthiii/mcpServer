# MCP Projects Overview

| **#** | **Description** | **MCP Servers Used** | **LLM / Framework** |
|:--:|:--|:--|:--|
| **1** |  `mcp_servers_external`: Demonstrates using multiple external MCP servers (Playwright, Airbnb, DuckDuckGo Search) to enable browsing, booking, and search automation via MCP client orchestration. | `@playwright/mcp`, `@openbnb/mcp-server-airbnb`, `duckduckgo-mcp-server` | **Groq**, **OpenAI**, MCP client (`mcp_use`) |
| **2** | `math_weather_multiserver`:  Implements two custom MCP servers — one for mathematical operations (`add`, `multiply`) and another for real-time weather data. Uses LangChain’s multi-server MCP client to let a Groq LLM dynamically invoke the correct server tools. | `MathMCP`, `WeatherMCP` | **Groq**, **LangChain MCP Client** |
