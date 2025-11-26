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
    # prompt = f"""
    

    # {strategy}


    # Once you display the results, Give me a short summary that is concise for the user to understand.

    # ### IMPORTANT

    # Give this output as a html <div> tag like this:

    # Note: Alignment must be to the left.

    # <div>
    # .... // your output
    # </div>

  





    # """

    # plannerPrompt = f"""
    # You are an expert Neo4j Cypher engineer.

    # You are given the complete schema of a Neo4j graph database above.  
    # Your ONLY job is to generate valid Cypher queries.

    # RULES:
    # 1. Always respond ONLY with Cypher queries.
    # 2. Do NOT explain anything.
    # 3. Do NOT add text, summaries, comments, or reasoning.
    # 4. Respect all node labels exactly as defined.
    # 5. Respect all relationship types and their directions exactly as defined.
    # 6. When the user asks a natural-language question, convert it directly into the correct Cypher query.
    # 7. If multiple interpretations exist, choose the most precise one based on the schema.
    # 8. NEVER invent properties or relationships not present in the schema.
    # 9. ALWAYS use the exact property names from the schema.
    # 10. NEVER output markdown, code fences, or backticks. Output plain Cypher only.

    # INSTRUCTION TO MODEL:
    # For every user question, produce one or more Cypher queries that answer the question as directly as possible.
    # Your output MUST contain only Cypher.
    # No comments.
    # No explanation.
    # No natural language.
    # """

    plannerPrompt= f'''



You are an expert Cypher Query Generator.  
Your ONLY job is to convert user natural-language requests into Cypher queries that strictly follow the EXACT structure and format shown below.

====================
### REQUIRED QUERY FORMAT (APPLIES TO ALL OUTPUT)
Every query you produce MUST follow this pattern:

match c = (<NODE_LABEL> {{<PROPERTY_FILTERS>}})-[]->() RETURN c

Where:
- <NODE_LABEL> is the correct label based on the user request (Control, Category, Domain, Function, SubControl, etc.)
- <PROPERTY_FILTERS> is a single map of properties requested by the user
- The output must ALWAYS include the relationship expansion: -[]->()
- The output must ALWAYS begin with: match c =
- The output must ALWAYS end with: RETURN c
- The entire query must ALWAYS be lowercase except property values and node labels

You must NEVER output:
- MATCH (c:Control...)
- MATCH (n:...)
- RETURN n
- A query without -[]->()
- A query without c = (...)
- Multiple MATCH statements
- Extra explanations, comments, or additional text
Only output ONE Cypher query following the exact structure.

====================
### DEFAULT RULE
If the user does not specify a framework, you MUST default to:
framework_id: "CIS CONTROLS"

====================
### EXAMPLES YOU MUST ALWAYS FOLLOW

1. Get all Controls under CIS:
match c = (:Control {{framework_id: "CIS CONTROLS"}})-[]->() RETURN c

2. Get Control by name:
match c = (:Control {{framework_id: "CIS CONTROLS", name: "<CONTROL_NAME>"}})-[]->() RETURN c

All future user prompts must follow this exact formatting and structure.

====================
### GENERAL RULES FOR ALL FUTURE QUERIES

1. ALWAYS use:
match c = (:<NODE_LABEL> {{<filters>}})-[]->() RETURN c

2. ALWAYS include framework_id when dealing with controls unless the user explicitly removes it.

3. ALWAYS keep all property filters inside ONE {{ }} object.

4. If the user asks for relationships, expand further but ALWAYS keep the root pattern EXACT:
match c = (...)

5. If the user refers to an ID (with a number), treat it as a string property.

6. If the user asks for something by name, use:
name: "<NAME>"

7. If the user asks for ALL items of a label, return:
match c = (:<LABEL> {{}})-[]->() RETURN c
but REMOVE {{}} only if no filters exist.

8. NEVER change the structure, ordering, or lowercase format.

====================
### FINAL RULE
Your output MUST ALWAYS BE:
match c = (<PATTERN>)-[]->() RETURN c

Nothing more. Nothing less.




'''


    prompt = f"""
    

    {strategy}


    Your task is to only give the cyper command of the user's request.
    Before you give me this command, you need to read and understand 
    everything that is there in the db through shcema I provided in the system prompt for you.

    Only then, must you give me the query.

    ### IMPORTANT

    Give this output as a html <div> tag like this:

    Note: Alignment must be to the left.

    <div>
    .... // your output
    </div>

  





    """

    ### END CODE HERE ###

    max_turns = 3

    messages = [

                {"role": "system", "content": "You are a senior data analyst who is an expertise with Neo4j Databses."},
                systemPrompt,
                {"role": "user", "content": plannerPrompt + prompt}
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





async def task_executor_openai2(query,tool_mapping, tool_defs, systemPrompt: dict ={"role": "system", "content":""}, model: str = "openai:gpt-4o-mini") -> str: 

    ### START CODE HERE ###

    # Define your prompt here. A multi-line f-string is typically used for this.
    prompt = f"""
    You are an expert Neo4j Cypher engineer with access to a tool that can execute Cypher queries.

    --------------------------------------------------------------------
    WHEN THE USER DIRECTLY PROVIDES A CYPHER QUERY
    --------------------------------------------------------------------
    - Detect that the message is already a Cypher query.
    - Do NOT rewrite, modify, optimize, or validate it.
    - Execute it using the provided tool.
    - Then respond with EXACTLY:

    <one-sentence description of what the query returns>
    <raw tool results converted into natural langauage>

    - No additional text.
    - No multi-line explanations.
    - No code fences.
    - No deviation in formatting.

    Example format (structure only):
    Description: Returns all outgoing relationships from the selected Control node.
    Results:
    <natural language converted tool output here>

    --------------------------------------------------------------------
    ABSOLUTE RESPONSE RULES
    --------------------------------------------------------------------
    - NEVER explain the schema unless asked.
    - NEVER include markdown code blocks or triple backticks.
    - NEVER output anything except:
    • A description + tool results (when running).
    - NEVER invent properties or relationships.
    - ALWAYS use labels, properties, and relationships EXACTLY as in the schema.

    --------------------------------------------------------------------
    USER's QUERY:
    {query}
    --------------------------------------------------------------------

    Follow all instructions strictly.

    After that give the final solution under a html tag like this:

    <div>
    .... // your output
    </div>
    """


 



    ### END CODE HERE ###

    max_turns = 3

    messages = [

                {"role": "system", "content": "You are an expert Neo4j Cypher engineer with access to a tool that can execute Cypher queries."},
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
