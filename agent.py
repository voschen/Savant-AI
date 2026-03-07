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
    tool_call: Literal["calulator", "search", "webpage_scrape"] | None
    tool_input: str | None 
    tool_result: str | None 
    retry: int 

class MessageValidator(BaseModel):
    role: Literal["user", "agent", "tool", "system"]
    content: str
    tool_call: Literal["calulator", "search", "webpage_scrape"] | None = None
    tool_input: str | None = None # I need to make pydantic verify the input format based on the tool, or either just make a loop that whenever the tool doesnt work repeat saying to the AI that the input format is wrongt 
    tool_result: str | None = None
    retry: int = 0

class State(TypedDict):
    messages: Annotated[list, operator.add]
    conversation_id: int


def validate_message(raw: dict) -> Message:
    """Validate with Pydantic, return plain TypedDict."""
    validated = MessageValidator(**raw)     
    return validated.model_dump()  

####################################################
################# Nodes and Edges ##################
####################################################


# Message here could either be from the user or the output of a previous tool that was used
async def thinker_node (state: State) -> dict:
    
    if state["messages"]["retry"] == 3:
        print("3rd retry failed, initiating a stop.")
        return None

    # edit later with a better algorithm to not overload the context with the entire chat while still having access to relevant previous information
    messages = state["messages"][-1] 
    context = state["messages"][-2] 
    # Another issue here is that the original prompt may be preceeded by many tool uses failures etc, so we will have up to 5-8 lists in bad scenarios just for one task
    async with httpx.AsyncClient() as client:

        response = await client.post(
            url="https://openrouter.ai/api/v1/chat/completions    ",
            headers = {
                "Authorization": f"Bearer { KEY}"
            },
            data = {
                "model": "arcee-ai/trinity-large-preview:free",
                "messages": [ 
                    {
                        "role": "user",
                        "content": f'''
                        Input query: {messages}
                        Context: {context}
                        Instructions: You are an AI assistant that must respond in JSON format with specific fields. Your response must be a valid JSON object with the following structure:
                        {
                          "role": "agent",
                          "content": "your response message here",
                          "tool_call": "calculator" OR "search" OR "webpage_scrape" OR null,
                          "tool_input": "input for the tool in the required format" OR null,
                          "tool_result": null,
                          "retry": 0
                        }
                        
                        When using tools:
                        - Calculator: Use when you need to perform calculations. Set "tool_call": "calculator" and "tool_input" to a mathematical expression with numbers and operators only (e.g., "2+2*3").
                        - Search: Use when you need to search for information. Set "tool_call": "search" and "tool_input" to your search query.
                        - Webpage Scrape: Use when you need to extract content from a webpage. Set "tool_call": "webpage_scrape" and "tool_input" to the URL.
                        
                        If no tool is needed, set "tool_call" to null and provide your response in "content".
                        
                        Your response must be valid JSON that can be parsed by Python's json.loads().
                        
                        '''
                    }
                ]    
          }
            )
        
        response.raise_for_status()
        return {"messages": [response["choices"]["message"]["content"]]}


def tool_router(state: State):
    if state["messages"]["tool_call"] == None:
        return "END"
    elif state["tool_call"].lower() == "calculator":
        return "tool_calculator"
    else:
       state["messages"].append({
        "role": "system",
        "content": f"Invalid tool call received; tool: {state["messages"][-1]["tool_call"]} - content: {state["messages"][-1]["content"]}",
        "tool_call": state["messages"][-1]["tool_call"],
        "tool_result": None,
        "retry": state["messages"][-1]["retry"] + 1 if state["messages"] else 1 # the first message has no prior
        })


async def calculator_node(state: State):
    # prompt: When calculating, output a JSON object with the key expression containing only numbers and standard operators.
    # Pydantic validation for no letters or special caharacters
        try:
            result = simpleeval.simple_eval(state["messages"][-1]["tool_input"])
            return result
        except Exception as e:
            raise e 
        


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

def user_input(user_message: str) -> dict:

    initial_state = {
        "messages": [],
        "tool_call": None,
        "tool_result": None
    }


# Run the code
result = graph.invoke(initial_state)  




# display(Image(graph.get_graph().draw_mermaid_png())) # draw the framework