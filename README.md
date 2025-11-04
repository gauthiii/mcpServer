
### MCP Overview

**Model Context Protocol (MCP)** is a standardized way for LLMs to interact with external tools and APIs.  
An **MCP Server** exposes tools or functions (like weather, math, or Gmail APIs), and an **MCP Client** connects these servers to an LLM so it can dynamically call the right tool during reasoning.

---

### MCP Projects Overview

| **S.NO** || **Project Description** | **MCP Servers Used** | **LLM / Framework** |
|:--|:--|:--|:--|
| 1 | **`mcp_servers_external`**<br> Demonstrates how multiple external MCP servers (like Playwright for browsing, Airbnb for booking, and DuckDuckGo for searching) can work together. The LLM uses these servers through a unified MCP client to automate real-world web actions such as searching, navigating sites, and simulating user tasks. | `@playwright/mcp`, `@openbnb/mcp-server-airbnb`, `duckduckgo-mcp-server` | **Groq**, **OpenAI**, MCP client (`mcp_use`) |
| 2 | **`math_weather_multiserver`**<br> Shows how two custom-built MCP servers can work together — one handles mathematical calculations (`add`, `multiply`), while the other fetches live weather data. A LangChain-based multi-server MCP client allows the LLM (Groq) to choose and call the right tool dynamically depending on the user’s query. | `MathMCP`, `WeatherMCP` | **Groq**, **LangChain MCP Client** |
| 3 | **`dataset_visualizer`**<br> Builds a dataset visualization assistant using custom MCP tools to analyze any dataframe variable (`df`). It can create JSON representations of the dataset, execute Python and HTML code dynamically, and save outputs as files. The system automatically suggests the best visualization type (e.g., scatter, bar, heatmap), generates the frontend visualization code, reflects on the output, and iteratively refines it based on LLM feedback. | `PythonMCP`, `VisualizationMCP`, `FileSaverMCP` | **Groq**, **OpenAI**, **LangGraph**, **Reflective Agent Loop** |
| 4 | **`amazon_search_analyzer`**<br> Automates Amazon product search and analysis through an MCP server connected to the Amazon search API and web scrapers. The system processes user queries, retrieves search results, compares alternatives, and generates detailed product analysis reports. Uses four coordinated agents — *Planner*, *Retriever*, *Analyzer*, and *Finalizer* — to simulate a complete decision-making workflow. | `Amazon search_products`, `Amazon scrape_product` | **Groq**, **OpenAI**, **LangGraph Multi-Agent**, **Tool Orchestration** |
| 5 | **`gmail_urgency_classifier`**<br> Uses Gmail MCP tools to authenticate via the Gmail API, read email content, and classify incoming messages based on urgency levels. The system runs through four agent stages — *Planner*, *Retriever*, *Classifier*, and *Finalizer* — to analyze subject lines and body text to determine priority (High, Medium, Low). It can run across **Ollama**, **Groq**, and **OpenAI** LLMs, offering flexible local and cloud inference. | `get_current_date`, `gmail_auth`, `gmail_unread_count`, `gmail_list`, `gmail_read` | **Ollama**, **Groq**, **OpenAI**, **LangChain MCP Agents** |


---

### Setup Instructions

#### Create and activate virtual environment (using `uv`)
```bash
uv venv .venv
source .venv/bin/activate  # (Mac/Linux)
# or
.venv\Scripts\activate     # (Windows)
```

#### Install required dependencies
```bash
uv pip install \
  "google-api-python-client>=2.186.0" \
  "google-auth-httplib2>=0.2.1" \
  "google-auth-oauthlib>=1.2.3" \
  "langchain-community>=0.4.1" \
  "langchain-core>=1.0.2" \
  "langchain-groq>=1.0.0" \
  "langchain-mcp-adapters>=0.1.12" \
  "langchain-openai>=1.0.1" \
  "langgraph>=1.0.2" \
  "mcp-use>=1.4.0" \
  "wikipedia>=1.4.0"
```


#### Create a .env file
```bash
GROQ_API_KEY=
OPENAI_API_KEY=
OPENWEATHER_API_KEY=
OPENWEATHER_BASE_URL=
ANTHROPIC_API_KEY=
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
```

#### Your MCP environment is now ready for multi-server orchestration with LangChain, Groq, and OpenAI.
