# Project 5: Gmail Urgency Classifier (`gmail_urgency_classifier`)

## 1. Project Overview

This project builds an **Intelligent Email Assistant** using a custom **Gmail MCP Server**. It automates the process of connecting to your Gmail inbox, reading relevant emails, and—most importantly—classifying them by urgency (High/Medium/Low) using a local or cloud-based LLM.

**Goal:** Create a privacy-aware agent that filters through inbox noise. Instead of just "listing emails," it reads the content and tells you: *"This email from Kotak Bank is urgent (payment due),"* vs *"This is just a newsletter."*

---

## 2. Architecture & Components

### A. The Gmail MCP Server (`server.py`)

This is the core "Tool Provider" running locally.

* **Authentication:** Uses Google's OAuth 2.0 flow. On the first run, it launches a browser window for you to log in and approve permissions. It stores the credentials in `token.json` for future use.
* **Tools Exposed:**
* `gmail_auth_status()`: Checks if the connection is active.
* `gmail_unread_count()`: Simple dashboard stat.
* `gmail_list(query)`: Advanced search (e.g., `from:bank subject:statement`).
* `gmail_read(message_id)`: Fetches the full body text of a specific email.



### B. The Agentic Workflow (`workflow.py`)

This script orchestrates a **Multi-Agent Pipeline** to process the data intelligently.

1. **Planner (Claude):** Analyzes the user request ("Find Kotak Bank emails from this week") and decides the search query logic.
2. **Task Executor (OpenAI):** Calls the `gmail_list` tool to find message IDs, then loops through them calling `gmail_read` to get the actual content.
3. **Urgency Classifier (Ollama/Local):** Takes the raw email body and subjects it to an analysis prompt: *"Is this urgent? Does it require action?"* It outputs a classified summary.

---

## 3. Google Cloud Platform (GCP) Setup Guide

To use this project, you must first authorize it to access your Gmail account via Google Cloud.

### Step 1: Create a Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click **Create Project** -> Name it `Gmail-MCP-Agent`.

### Step 2: Enable Gmail API

1. In the sidebar, go to **APIs & Services** -> **Library**.
2. Search for **"Gmail API"**.
3. Click **Enable**.

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** -> **OAuth consent screen**.
2. Select **External** (unless you have a G-Suite organization) -> **Create**.
3. Fill in the App Name ("Gmail Agent") and User Support Email.
4. **Important:** Under "Test Users", add your own email address. (Since the app is in "Testing" mode, only listed users can log in).

### Step 4: Create Credentials

1. Go to **APIs & Services** -> **Credentials**.
2. Click **Create Credentials** -> **OAuth client ID**.
3. Application Type: **Desktop App**.
4. Name: `Gmail-MCP-Desktop`.
5. Click **Create**.
6. **Download JSON:** You will see a popup with your Client ID and Secret. Click **Download JSON**.
7. Rename this file to `credentials.json` (or copy the ID/Secret into your `.env` file as `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET`).

---

## 4. Code Breakdown

### `server.py` (The Connector)

* **`_credentials()`**: Handles the OAuth "dance." If `token.json` is missing/expired, it pauses the script and opens your web browser to `localhost` to let you sign in.
* **`_decode_body()`**: Email bodies are messy (HTML, base64 encoded). This helper function strips away the HTML tags (`<br>`, `<div>`) to give the LLM clean text to analyze, saving tokens.

### `workflow.py` (The Brain)

* **Model Routing:** This project demonstrates advanced routing.
* *Strategic Planning* is done by **Claude** (known for good reasoning).
* *Tool Execution* is done by **OpenAI** (reliable tool calling).
* *Privacy-Sensitive Classification* is done by **Ollama** (running locally), so the full text of your private emails doesn't necessarily have to leave your machine for the final analysis step if configured strictly.



---

## 5. How to Run

### Prerequisites

* `.env` file with `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET`.
* Ollama running locally (if using the classifier agent).

### Step 1: Start the Server (First Run)

Run the server manually the first time to generate the token.

```bash
python server.py

```

* **Action:** A browser window will open. Sign in with your Google account and allow access.
* **Result:** A `token.json` file will appear in your project folder. You can now stop the server (Ctrl+C).

### Step 2: Run the Agentic Workflow

Now that authentication is cached, run the full pipeline.

```bash
python workflow.py

```

### Expected Output

1. **Planner:** "Strategy: Search for 'Kotak Bank' emails received in the last 7 days."
2. **Executor:** "Found 3 emails. Reading Email ID 18e..."
3. **Classifier:**
* *Email 1:* "Subject: Transaction Alert. **Urgency: High**. Action: Verify transaction of $50."
* *Email 2:* "Subject: New Offers. **Urgency: Low**. Action: None."



---
