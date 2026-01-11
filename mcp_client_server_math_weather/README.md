# Project 2: Math & Weather Multi-Server System (`math_weather_multiserver`)

## 1. Project Overview

This project demonstrates how to build **custom MCP Servers** from scratch using Python. While Project 1 used pre-built Node.js tools, this project teaches you how to write your own functions (Math logic and Weather API integration) and expose them to an LLM.

**Goal:** Create a "Hybrid" agent that connects to two different custom servers simultaneously—one running locally as a subprocess (Math) and one running as a web service (Weather)—allowing the LLM to route queries to the correct tool dynamically.

---

## 2. Architecture

This project highlights two different **Transport Protocols** supported by MCP:

1. **Math Server (Stdio Transport):**
* **Type:** Local Subprocess.
* **How it works:** The client launches the script (`python mathserver.py`) directly and communicates via Standard Input/Output.
* **Use Case:** Ideal for sensitive local tools or lightweight scripts.


2. **Weather Server (HTTP/SSE Transport):**
* **Type:** Web Service.
* **How it works:** This server runs independently on `localhost:8000`. The client connects to it via URL (`http://localhost:8000/mcp`).
* **Use Case:** Ideal for distributed systems, microservices, or sharing tools across a network.



---

## 3. Server Code Breakdown

### A. The Math Server (`mathserver.py`)

This uses **FastMCP** to quickly turn standard Python functions into AI tools.

* **`@mcp.tool()`:** This decorator automatically generates the tool definition (JSON schema) required by the LLM.
* **`transport="stdio"`:** Tells the server to listen to the command line input.

### B. The Weather Server (`weather_server.py`)

This connects to the **OpenWeatherMap API**.

* **Dependencies:** Requires `requests` and a valid `OPENWEATHER_API_KEY`.
* **Logic:** It fetches current weather and forecast data, cleans the JSON payload (removing unnecessary fields to save token usage), and returns a compact dictionary.
* **`transport="streamable-http"`:** Runs a uvicorn/Starlette web server, making the tools accessible via HTTP.

---

## 4. The Client (`client.py`)

The client uses `MultiServerMCPClient` to aggregate tools from both sources into a single list for the LLM.

```python
client = MultiServerMCPClient(
    {
        "math": {
            # Stdio Connection: The client starts this process for you
            "command": "python",
            "args": ["mathserver.py"],
            "transport": "stdio"
        },
        "weather": {
            # HTTP Connection: The client expects this to be already running
            "url": "http://localhost:8000/mcp",
            "transport": "streamable_http"
        }
    }
)

```

**The Agent:**
We use **LangGraph's `create_react_agent**` combined with **Groq (`llama-3.1-8b`)**. The ReAct (Reason + Act) pattern allows the model to "think" before choosing a tool:

* *User:* "What is 3 + 5?" -> *Agent:* Calls `Math.add(3, 5)`.
* *User:* "Weather in California?" -> *Agent:* Calls `Weather.get_weather("California")`.

---

## 5. How to Run

Because the Weather server uses HTTP, it must be started *separately* before you run the client.

### Prerequisites

* Ensure `OPENWEATHER_API_KEY` and `GROQ_API_KEY` are in your `.env` file.
* Install dependencies (`fastmcp`, `langchain-groq`, `langgraph`, `requests`).

### Step 1: Start the Weather Server

Open a terminal and run the weather script. It will hang (listen) on port 8000.

```bash
# Terminal 1
python weather_server.py
# Output: Running on http://0.0.0.0:8000

```

### Step 2: Run the Client

Open a **second** terminal. This script will automatically start the Math server (via stdio) and connect to the running Weather server.

```bash
# Terminal 2
python client.py

```

### Expected Output

You will see the agent handle two distinct tasks in sequence:

1. **Math Task:**
* *Query:* "what's (3 + 5) x 12?"
* *Action:* Calls `add(3, 5)` then `multiply(8, 12)`.
* *Result:* "96"


2. **Weather Task:**
* *Query:* "what is the weather in California?"
* *Action:* Calls `get_weather(city="California")`.
* *Result:* "It is currently 22°C in California with clear skies..."
