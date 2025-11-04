import aisuite as ai
CLIENT = ai.Client()


def planner_claude(query, tool_defs, model: str = "anthropic:claude-haiku-4-5") -> str: 
    
    ### START CODE HERE ###

    # Define your prompt here. A multi-line f-string is typically used for this.
    prompt = f'''
    
    The user has a task: {query}

    Your task is to first think and plan how to execute this.

    You have access to tools. You can plan whether to use those tools or not.

    After thinking and planning, provide the steps how to execute this. No additional information.
    
    ''' 

    ### END CODE HERE ###
    
    # Get a response from the LLM by creating a chat with the client.
    response = CLIENT.chat.completions.create(
        model=model,
        messages=[

            {"role": "system", "content": "You are a meticulous shopping assistant."},
            {"role": "user", "content": prompt}
            ],
        tools = tool_defs,
        temperature=1.0,
    )

    return response.choices[0].message.content


def planner_ollama(query, tool_defs, model: str = "ollama:gemma3:latest") -> str:
    """
    Use a local Ollama model as a planner.
    It will *not* actually call tools, it only reasons about them in text.
    """

    # Turn tool definitions into a readable list for the prompt
    tool_names = []
    for t in tool_defs:
        fn = t.get("function", {})
        name = fn.get("name", "unknown_tool")
        desc = fn.get("description", "")
        tool_names.append(f"- {name}: {desc}")

    tools_text = "\n".join(tool_names) if tool_names else "- (no tools configured)"

    prompt = f"""
    The user has a task: {query}

    You have access to the following tools (by name only; you will NOT execute them here):
    {tools_text}

    Your job is to:
    1. Think step by step about how you would solve the task.
    2. Decide *whether* you would use any of these tools and why.
    3. Output a clear, numbered list of steps to execute this plan.

    Important:
    - Do NOT actually call any tools.
    - Do NOT add extra commentary; just the steps.
    """

    response = CLIENT.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a meticulous shopping assistant and planner."},
            {"role": "user", "content": prompt},
        ],
        # ❌ No `tools` here — Ollama /api/chat doesn't support OpenAI-style tools
        temperature=0.6,
    )

    return response.choices[0].message.content