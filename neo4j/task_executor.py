import aisuite as ai
CLIENT = ai.Client()

import json

# ollama:gemma3:latest


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

    Your task is to first think and plan how to execute this.


    You have access to tools. You can plan how to do this by using the tools only.

    After thinking and planning, provide the steps how to execute this. No additional information.

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
            {"role": "system", "content": "You are a task planner."},
            {"role": "user", "content": prompt},
        ],
        # ❌ No `tools` here — Ollama /api/chat doesn't support OpenAI-style tools
        temperature=0.6,
    )

    return response.choices[0].message.content
    

async def task_executor_openai(strategy,tool_mapping, tool_defs, systemPrompt: dict ={"role": "system", "content":""}, model: str = "openai:gpt-4o-mini") -> str: 

    ### START CODE HERE ###

    # Define your prompt here. A multi-line f-string is typically used for this.
    prompt = f"""
    

    {strategy}


    Once you display the results, Give me a short summary that is concise for the user to understand.

    ### IMPORTANT

    Give this output as a html <div> tag like this:

    Note: Alignment must be to the left.

    <div>
    .... // your output
    </div>

  





    """

    ### END CODE HERE ###

    max_turns = 7

    messages = [

                {"role": "system", "content": "You are a senior data analyst who is an expertise with Neo4j Databses."},
                systemPrompt,
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
