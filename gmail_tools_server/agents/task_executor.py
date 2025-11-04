import aisuite as ai
CLIENT = ai.Client()

import json

async def task_executor_groq(strategy,tool_mapping, tool_defs, model: str = "groq:llama-3.1-8b-instant") -> str:
    """
    Groq-specific agent loop that uses MCP tools to execute tasks.
    Differs from the OpenAI version only in how it formats `role: "tool"` messages
    (no `tool_name` field, which Groq rejects).
    """

    prompt = f"""
    So you need to execute the following stratgey planned for the user:

    {strategy}

    If found, list the emails with just the subject and date.

    Execute all the necessary steps required to accomplish the user's goal.
    Use tools if necessary.




    """

    max_turns = 3

    messages = [
        {"role": "system", "content": "You are an amazing shopping assistant who is also a smart webscraper and data analyst."},
        {"role": "user", "content": prompt},
    ]

    final_text = ""

    for i in range(max_turns):
        # print(f"\n**********************************************************************************\n")
        print(f"Attempt : {i+1}")

        # Call Groq chat completions
        response = CLIENT.chat.completions.create(
            model=model,
            messages=messages,
            tools=tool_defs,
            temperature=1.0,
        )

        msg = response.choices[0].message

        # Build assistant message we send back next turn
        assistant_msg = {
            "role": msg.role,
            "content": msg.content or "",
        }

        # Keep tool_calls so Groq knows why tool messages follow
        if getattr(msg, "tool_calls", None):
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]

        messages.append(assistant_msg)

        # If no tool calls, this is the final answer
        if not getattr(msg, "tool_calls", None):
            final_text = msg.content
            print("✅ Final answer:")
            print(final_text)
            break

        # print("Tool Calls Detected:")
        # print(msg.tool_calls)

        # Execute each requested tool
        for tool_call in msg.tool_calls:
            tool_id = tool_call.id
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments

            args = json.loads(tool_args or "{}")

            print(f"Calling tool: {tool_name} with args: {tool_args}")

            tool = tool_mapping[tool_name]
            tool_response = await tool.coroutine(**args)

            # print(f"Tool response: {tool_response}")

            # 🔴 IMPORTANT for Groq:
            # - No `tool_name` field (Groq rejects it)
            # - Just role, tool_call_id, content
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": str(tool_response),
                }
            )

    return final_text


# ollama:gemma3:latest
# ollama:qwen3:4b
# ollama:gpt-oss:20b-cloud

async def task_executor_ollama(
    strategy: str,
    tool_mapping,
    tool_defs,  # kept for signature symmetry; not used directly
    model: str = "ollama:gemma3:latest",
) -> str:
    """
    Ollama-specific executor.

    Because Ollama's /api/chat doesn't support OpenAI-style tools/tool_calls,
    we do a two-phase flow:

    1) Ask the model to output a JSON list of tool calls to make.
    2) Execute those MCP tools in Python.
    3) Send the tool results back to Ollama and ask for the final answer.
    """

    # 1️⃣ Ask Ollama which tools to call and with what arguments (JSON-only)
    available_tools = ", ".join(tool_mapping.keys())

    planning_prompt = f"""
You are an execution agent. The high-level strategy to follow is:

{strategy}

You have access to the following tools, which my code can execute for you:

{available_tools}

Your job now is ONLY to propose which tools to call, in what order, and with what arguments.
Return STRICTLY a JSON array, no prose, of the form:

[
  {{
    "tool_name": "<one of: {available_tools}>",
    "args": {{
      "...": "..."
    }},
    "purpose": "short description of why you are calling this tool"
  }},
  ...
]

Constraints:

- Make sure "args" is a valid JSON object, not a string.
- Do NOT include any text before or after the JSON.
"""

    plan_response = CLIENT.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a meticulous planner that outputs ONLY valid JSON when asked.",
            },
            {"role": "user", "content": planning_prompt},
        ],
        temperature=0.3,
    )

    tool_plan_text = plan_response.choices[0].message.content or "[]"

    try:
        proposed_calls = json.loads(tool_plan_text)
        if not isinstance(proposed_calls, list):
            proposed_calls = []
    except json.JSONDecodeError:
        # If the model ignored instructions and didn't give valid JSON,
        # fall back to no tool calls.
        proposed_calls = []

    # 2️⃣ Execute the proposed MCP tool calls
    executed_results = []

    for call in proposed_calls:  # safety cap at 5
        tool_name = call.get("tool_name")
        args = call.get("args", {}) or {}
        purpose = call.get("purpose", "")

        if tool_name not in tool_mapping:
            continue

        tool = tool_mapping[tool_name]

        # args must be a dict
        if not isinstance(args, dict):
            continue

        print(f"[Ollama executor] Calling tool: {tool_name} with args: {args}")

        try:
            result = await tool.coroutine(**args)
        except Exception as e:
            result = f"ERROR calling tool {tool_name}: {e}"

        executed_results.append(
            {
                "tool_name": tool_name,
                "args": args,
                "purpose": purpose,
                "result": str(result),
            }
        )

    # 3️⃣ Ask Ollama to synthesize final answer based on strategy + tool results
    results_json = json.dumps(executed_results, indent=2)

    final_prompt = f"""
The original execution strategy was:

{strategy}

If found, list the emails with just the subject and date.

You (through my code) have now executed the following tool calls, with these results:

{results_json}

Now, write the final response to the user that accomplishes their goal.
- Use the tool results as your evidence.
- Summarize and compare as needed.
- Do NOT mention tools, JSON, or internal steps.
- Just give a clear, concise answer as a shopping assistant.
"""

    final_response = CLIENT.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are an amazing shopping assistant and data analyst.",
            },
            {"role": "user", "content": final_prompt},
        ],
        temperature=0.6,
    )

    final_text = final_response.choices[0].message.content or ""
    return final_text


async def task_executor_openai(strategy,tool_mapping, tool_defs, model: str = "openai:gpt-4o-mini") -> str: 

    ### START CODE HERE ###

    # Define your prompt here. A multi-line f-string is typically used for this.
    prompt = f"""
    So you need to execute the following stratgey planned for the user:

    {strategy}

    If found, list the emails with just the subject and date.

    Execute all the necessary steps required to accomplish the user's goal.
    Use tools if necessary.




    """

    ### END CODE HERE ###

    max_turns = 3

    messages = [

                {"role": "system", "content": "You are a smart webscraper and data analyst."},
                {"role": "user", "content": prompt}
                ]

    for i in range(max_turns):

        print(f"\n**********************************************************************************\n")

        print(f"Attempt : {i+1}")
    
        # Get a response from the LLM by creating a chat with the client.
        response = CLIENT.chat.completions.create(
            model=model,
            messages=messages,
            tools = tool_defs,
            temperature=1.0,
        )

        msg = response.choices[0].message

        assistant_msg = {
            "role": msg.role,
            "content": msg.content or ""
        }

        # IMPORTANT: keep tool_calls if present
        if getattr(msg, "tool_calls", None):
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]

        messages.append(assistant_msg)



        if not msg.tool_calls:      
            final_text = msg.content
            print("✅ Final answer:")
            print(final_text)
            break

        else:
            print("Tool Calls Detected:")
            print(msg.tool_calls)


        for tool_call in msg.tool_calls:

            tool_id = tool_call.id
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments

            args = json.loads(tool_args or "{}")  


            print(f'Calling tool: {tool_name} with args: {tool_args}')

            # tool_response = tool_mapping[tool_name](**args)

            tool = tool_mapping[tool_name]

            # 🔄 ASYNC EXECUTION
            # if hasattr(tool, "ainvoke"):
            #     tool_response = await tool.ainvoke(args)
            # else:
            #     tool_response = tool.invoke(args)

            tool_response = await tool.coroutine(**args)

            print(f'Tool response: {tool_response}')

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "tool_name": tool_name,         
                    "content": str(tool_response)    
                }
            )



    return final_text
