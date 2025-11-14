import os
import aiohttp
import json
import requests
from typing import List, Dict
from src.app import mcp

@mcp.tool(
    name="chutes_chat_stream",
    description="Sends a prompt to a Chutes LLM and gets a streaming response. Use this for real-time applications."
)
async def stream_chat(
    messages: List[Dict[str, str]],
    model: str = "deepseek-ai/DeepSeek-R1-0528",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """
    Sends a chat message to the Chutes LLM endpoint and streams the response.

    :param messages: A list of messages in the conversation.
    :param model: The model to use for the completion.
    :param temperature: The temperature for the completion.
    :param max_tokens: The maximum number of tokens to generate.
    :return: The full response from the LLM.
    """
    api_token = os.getenv("CHUTES_API_TOKEN")
    if not api_token:
        return "Error: CHUTES_API_TOKEN environment variable not set."

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    body = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    full_response = ""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://llm.chutes.ai/v1/chat/completions",
            headers=headers,
            json=body
        ) as response:
            async for line in response.content:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(data)
                        if chunk_data["choices"][0]["delta"].get("content"):
                            chunk_content = chunk_data["choices"][0]["delta"]["content"]
                            full_response += chunk_content
                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        print(f"Error processing chunk: {e}")
    
    return full_response

@mcp.tool(
    name="chutes_chat",
    description="Sends a prompt to a Chutes LLM and gets a single response. Use this for non-streaming applications."
)
def chat(
    messages: List[Dict[str, str]],
    model: str = "deepseek-ai/DeepSeek-R1-0528",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """
    Sends a chat message to the Chutes LLM endpoint and gets a single response.

    :param messages: A list of messages in the conversation.
    :param model: The model to use for the completion.
    :param temperature: The temperature for the completion.
    :param max_tokens: The maximum number of tokens to generate.
    :return: The content of the response from the LLM.
    """
    api_token = os.getenv("CHUTES_API_TOKEN")
    if not api_token:
        return "Error: CHUTES_API_TOKEN environment variable not set."

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(
            "https://llm.chutes.ai/v1/chat/completions",
            headers=headers,
            json=body
        )
        response.raise_for_status()
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Error calling Chutes API: {e}"
    except (KeyError, IndexError) as e:
        return f"Error parsing response from Chutes API: {e}"
