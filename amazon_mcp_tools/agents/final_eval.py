import aisuite as ai
CLIENT = ai.Client()

import json

async def final_eval_ollama(
    reflection,
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
You are an evaluating agent.

And the results obtained were:

{reflection}

You need to get me the complete details of the product that was recommended:

    - price
    - rating
    - delivery time
    - benefits
    - reviews
    - discounts if any
    - warranty if any
    - durability
    - the best positive review if any
    - the worst negative review if any
    - the availablity
    - the product url

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
- Don't request more than 5 tool calls total.
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
The original results obtained were:

{reflection}

You need to get me the complete details of the product that was recommended:

    - price
    - rating
    - delivery time
    - benefits
    - reviews
    - discounts if any
    - warranty if any
    - durability
    - the best positive review if any
    - the worst negative review if any
    - the availablity
    - the product url

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