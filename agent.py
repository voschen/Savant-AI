

import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated, Sequence, Any
from IPython.display import Image, display
import operator

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END, START

import httpx

load_dotenv()
KEY = os.getenv("OPENROUTER_API_KEY")

#######################################################
################## Defining state #####################
#######################################################

class State(TypedDict):
    messages: Annotated[list, operator.add] # Expected to log: user queries, AI responses, tool uses
    tool_call: str | None
    tool_result: str | None



####################################################
################# Nodes and Edges ##################
####################################################



async def thinker_node (state: State) -> dict:

    messages = state["messages"]

    async with httpx.AsyncClient() as client:

        response = await client.post(

            url="https://openrouter.ai/api/v1/chat/completions",
            headers = {
                "Authorization": f"Bearer {KEY}"
            },
            data = {
                "model": "",
                "messages": [ 
                    {
                        "role": "user",
                        "content": "message"
                    }
                ]    
          }
            )
        
        response.raise_for_status()
        return {"messages": [response.json()]}
    

builder = StateGraph(State)
builder.add_node(thinker_node)
builder.add_edge(START, "thinker_node")
graph = builder.compile()




# display(Image(graph.get_graph().draw_mermaid_png())) # draw the framework