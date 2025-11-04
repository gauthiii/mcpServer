from mcp.server.fastmcp import FastMCP
from datetime import datetime
from langchain_community.retrievers import WikipediaRetriever


mcp=FastMCP("Twitter Server")

@mcp.tool()
def wikiSearch(query: str)->str:
    """_summary_
    Searches Wikipedia for the given query and returns a summary of the most relevant article.
    """

    retriever = WikipediaRetriever()

    docs = retriever.invoke(query)

    if docs:
        summary = docs[0].page_content
        return summary
    
    return "No relevant Wikipedia article found."



@mcp.tool()
def get_date_time()->str:
    """_summary_
    Displays the current date and time in this specific format: Day(day suffix) Month Year, Hour:Minute AM/PM
    """

    # Get the current date and time
    now = datetime.now()

    # Determine the correct day suffix
    if 10 <= now.day % 100 <= 20:
        day_suffix = 'th'
    else:
        day_suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(now.day % 10, 'th')

    # Use now.day directly to avoid zero-padding
    formatted_time = now.strftime(f"{now.day}{day_suffix} %B %Y, %I:%M %p")

    print("Function called at: "+formatted_time)

    return formatted_time







#The transport="stdio" argument tells the server to:

#Use standard input/output (stdin and stdout) to receive and respond to tool function calls.



if __name__=="__main__":
    mcp.run(transport="stdio")