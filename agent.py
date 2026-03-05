i was thinking whether to evaluate not with pydantic but by simply seeing if there as an error running simpleeval, cause maybe its lighter than pydantic and wont requiremt me to write more code? since ill have to write that error handling there anyways.


# features to add: Ask window for when he wanna perform an action, ill click allow or not. 
# add RAG features in this project
# Allow agent to read files and give it multimodal capabilities (pdf for example)
# A tool that allows the agent to query its own performance metrics (e.g., "How many tokens have I used?", "Is the server busy?").



import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated, Sequence, Any, Literal
from IPython.display import Image, display
import operator

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END, START

import httpx
import simpleeval

load_dotenv()
KEY = os.getenv("OPENROUTER_API_KEY")

#######################################################
################## Defining state #####################
#######################################################



class Message(TypedDict):
    role: Literal["user", "agent", "tool", "system"]
    content: str 
    tool_call: str | None
    tool_result: str | None
    retry: int 

class State(TypedDict):
    messages: Annotated[list, operator.add]
    conversation_id: int

tool_list = [
    "calulator", 
    "search",
    "webpage_scrape",
    ]

####################################################
################# Nodes and Edges ##################
####################################################


# Message here could either be from the user or the output of a previous tool that was used
async def thinker_node (state: State, message) -> dict:
    
    if state["messages"]["retry"] == 3:
        print("3rd retry failed, initiating a stop.")
        return None

    messages = state["messages"]
    async with httpx.AsyncClient() as client:

        response = await client.post(
            url="https://openrouter.ai/api/v1/chat/completions  ",
            headers = {
                "Authorization": f"Bearer {KEY}"
            },
            data = {
                "model": "arcee-ai/trinity-large-preview:free",
                "messages": [ 
                    {
                        "role": "user",
                        "content": message
                    }
                ]    
          }
            )
        
        response.raise_for_status()
        return {"messages": [response["choices"]["message"]["content"]]}


async def tool_router(state: State):
    if state["messages"]["tool_call"] == None:
        return "END"
    elif state["tool_call"].lower == "calculator":
        return "tool_calculator"
    else:
        # Send a message to the thinker node saying the tool call was invalid
        # update loop counter so that we stop at 3 retries, and try again. it's error handling
        state["messages"][-1]["retry"] += 1 
        return "thinker_node"9


async def tool_calculator(state: State):
    # prompt: When calculating, output a JSON object with the key expression containing only numbers and standard operators.
    # Pydantic validation for no letters or special caharacters
    return None

####################################################
################# Graph Design #####################
####################################################

builder = StateGraph(State)
builder.add_node(thinker_node)
builder.add_edge(START, "thinker_node")
builder.add_conditional_edges("thinker_node", "tool_router")
graph = builder.compile()   

####################################################
################# Initiation #######################
####################################################


initial_state = {
    "messages": [],
    "tool_call": None,
    "tool_result": None
}


# Run the code
result = graph.invoke(initial_state)  




# display(Image(graph.get_graph().draw_mermaid_png())) # draw the framework