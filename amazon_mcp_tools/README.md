# Project 4: Amazon Search & Analyzer Agent (`amazon_search_analyzer`)

## 1. Project Overview

This project implements a **Multi-Agent E-commerce Assistant** powered by a custom MCP Server. It goes beyond simple product search by orchestrating a team of agents to plan, execute, reflect on, and finalize product recommendations.

**Goal:** Automate the entire "Smart Shopper" journey—from understanding a vague user request (e.g., "Find the best phone under $1000") to scraping live data, comparing technical specs, and providing a reasoned final recommendation.

---

## 2. Architecture & Components

The system is built on a **Client-Server** model where the "Brain" (Client) is separated from the "Hands" (Server).

### A. The Amazon MCP Server (`server.py`)

This is a custom `FastMCP` server that acts as the interface to Amazon.com.

* **Tools Provided:**
* `search_products(query, max_results)`: Performs a keyword search on Amazon and parses the results page to return a list of products with prices and ratings.
* `scrape_product(product_url)`: Visits a specific product page to extract deep details like full description, availability, and review counts.


* **Tech Stack:** Uses `httpx` for async web requests and `BeautifulSoup` for HTML parsing. It includes logic to handle Amazon's HTML structure (CSS selectors for price, title, image).

### B. The Agentic Client (`client.py`)

This is the "Brain" that orchestrates the workflow. Instead of a single LLM call, it runs a **Sequential Multi-Agent Chain**:

1. **Planner Agent:** Breaks the user's shopping goal into specific steps (e.g., "1. Search for 'phones under $1000', 2. Pick the top 3 rated ones, 3. Scrape details for each").
2. **Task Executor Agent:** Executes the plan by calling the MCP tools (`search_products`, `scrape_product`).
3. **Reflector Agent:** Reviews the gathered data. It asks: "Did I get enough info? Is the price actually under $1000?" If data is missing, it might trigger more tool calls.
4. **Finalizer Agent:** Synthesizes everything into a final user-friendly report.

---

## 3. Code Breakdown

### `server.py` (The Scraper)

* **`FastMCP("Amazon Scraper")`**: Initializes the server.
* **`clean_price`**: A helper utility to sanitize messy price strings (e.g., "$999.99" -> 999.99).
* **`extract_product_data`**: The core scraping logic. It uses a list of fallback CSS selectors (`#productTitle`, `h1.a-size-large`) to ensure robustness even if Amazon changes its page layout slightly.

### `client.py` (The Orchestrator)

* **`MultiServerMCPClient`**: Connects to the local server defined in `config.json`.
* **`tool_def_maker.py`**: A bridge utility. It converts LangChain's tool definitions into the specific JSON format required by OpenAI/Ollama APIs so the agents know *how* to call the tools.
* **Agent Modules (`agents.*`)**: The code references imported agents (`agents.planner`, `agents.task_executor`, etc.), showing a modular design where each agent's prompt and logic are kept in separate files.

---

## 4. How to Run

### Prerequisites

* **Ollama:** The client code is configured to use `ollama` (e.g., `llama3` or `gemma2`) for the agent logic, making this a fully local or hybrid solution.
* **Dependencies:** `mcp`, `beautifulsoup4`, `httpx`, `langchain-mcp-adapters`.

### Step 1: Start the Amazon Server

You need to run the server so it listens for requests.

```bash
# Terminal 1
python server.py
# Output: Amazon Scraper MCP server running on stdio...

```

*(Note: In a real deployment, the `client.py` usually starts this server automatically via the `config.json` command, similar to Project 1. Ensure `config.json` points to `python server.py`)*

### Step 2: Run the Client

```bash
# Terminal 2
python client.py

```

### Expected Output

1. **Planner:** Output a strategy like "I will search for phones..."
2. **Executor:** You'll see logs of it calling `search_products("phones under 1000")`.
3. **Reflector:** "I found 5 phones, but need more details on the Pixel 8."
4. **Final Eval:** "Based on the search, the best phone is..."

---

## 5. Why is this "Agentic"?

A simple script would just search Amazon and dump the first 5 links.
**This system is Agentic because:**

1. **It Plans:** It doesn't just react; it formulates a multi-step strategy.
2. **It Verifies:** The Reflector agent acts as a quality control layer, ensuring the "result" actually matches the user's budget and criteria.
3. **It Adapts:** If the search returns no results, the agents can theoretically decide to try a different query (depending on the Executor logic).
