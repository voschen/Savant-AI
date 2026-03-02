
import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated, Sequence, Any
import operator

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

import httpx


KEY = os.getenv("OPENROUTER_API_KEY")
messages = []

async def thinker_agent (messages: list):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers = {
                "Authorization": f"Bearer {KEY}"
            },
            json = {
                "role": "user",
                "content": messages
            }
            )
        
        response.raise_for_status()
        return response.json()


