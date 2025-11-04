# groq:llama-3.1-8b-instant
# openai:gpt-4o-mini
# anthropic:claude-haiku-4-5

import aisuite as ai
CLIENT = ai.Client()
import json


async def compare_products_openai(tool_mapping, tool_defs, model: str = "openai:gpt-4o-mini") -> str: 

    ### START CODE HERE ###

    # Define your prompt here. A multi-line f-string is typically used for this.
    prompt = f'''
    
    Can you compare the prices between a LG and a Sony TV?

    Assume the latest brands for both the models.
    
    ''' 

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






async def compare_products_groq(tool_mapping, tool_defs, model: str = "groq:llama-3.1-8b-instant") -> str:
    """
    Groq-specific agent loop that uses MCP tools to compare LG vs Sony TV prices.
    Differs from the OpenAI version only in how it formats `role: "tool"` messages
    (no `tool_name` field, which Groq rejects).
    """

    prompt = """
    Can you compare the prices between an LG TV and a Sony TV?
    Assume the latest popular models for both brands.
    """

    max_turns = 3

    messages = [
        {"role": "system", "content": "You are a smart webscraper and data analyst."},
        {"role": "user", "content": prompt},
    ]

    final_text = ""

    for i in range(max_turns):
        print(f"\n**********************************************************************************\n")
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

        print("Tool Calls Detected:")
        print(msg.tool_calls)

        # Execute each requested tool
        for tool_call in msg.tool_calls:
            tool_id = tool_call.id
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments

            args = json.loads(tool_args or "{}")

            print(f"Calling tool: {tool_name} with args: {tool_args}")

            tool = tool_mapping[tool_name]
            tool_response = await tool.coroutine(**args)

            print(f"Tool response: {tool_response}")

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