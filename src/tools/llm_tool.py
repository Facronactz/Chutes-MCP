import os
import aiohttp
import json
from loguru import logger
import requests
from typing import List, Dict, Annotated
from fastmcp import Context
from pydantic import Field
from fastmcp.exceptions import ToolError
from src.mcp_instance import mcp
from src.config import config

@mcp.tool(
    name="chutes_chat_stream",
    description="Sends a prompt to a Chutes LLM and gets a streaming response. Use this for real-time applications.",
    annotations={
        "title": "Chutes Chat Stream",
        "readOnlyHint": True,  # It reads from LLM, doesn't modify environment
        "openWorldHint": True   # It interacts with an external LLM API
    }
)
async def stream_chat(
    context: Context,
    messages: Annotated[List[Dict[str, str]], Field(description="A list of message objects, each with a 'role' (e.g., 'user', 'assistant') and 'content' string. Represents the conversation history.")],
    model: Annotated[str, Field(description="The model to use for the completion.")] = config.get("chutes.models.llm"),
    temperature: Annotated[float, Field(description="The sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.", ge=0.0, le=2.0)] = 0.7,
    max_tokens: Annotated[int, Field(description="The maximum number of tokens to generate in the chat completion. The token count of your prompt plus max_tokens cannot exceed the model's context length.", ge=1)] = 1024,
) -> str:
    """
    Sends a chat message to the Chutes LLM endpoint and streams the response.

    :param messages: A list of messages in the conversation.
    :param model: The model to use for the completion.
    :param temperature: The temperature for the completion.
    :param max_tokens: The maximum number of tokens to generate.
    :return: The full response from the LLM.
    """
    await context.info("Entering stream_chat function.")
    await context.debug(f"Stream Chat Parameters: model={model}, temperature={temperature}, max_tokens={max_tokens}")

    api_token = config.get("chutes.api_token")
    if not api_token:
        await context.warning("CHUTES_API_TOKEN environment variable not set for stream_chat.")
        raise ToolError("CHUTES_API_TOKEN environment variable not set.")

    llm_endpoint = config.get("chutes.endpoints.llm")
    if not llm_endpoint:
        await context.warning("LLM endpoint not configured in config.yaml for stream_chat.")
        raise ToolError("LLM endpoint not configured in config.yaml.")

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
    try:
        await context.report_progress(progress=0, total=2, message="Preparing LLM streaming request.")
        async with aiohttp.ClientSession() as session:
            await context.report_progress(progress=1, total=2, message="Connecting to LLM API...")
            async with session.post(
                llm_endpoint,
                headers=headers,
                json=body
            ) as response:
                response.raise_for_status()  # Raise an exception for bad status codes
                await context.debug(f"Stream chat request sent to {llm_endpoint}, status: {response.status}")
                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            await context.debug("Stream finished with [DONE] signal.")
                            break
                        try:
                            chunk_data = json.loads(data)
                            if chunk_data["choices"][0]["delta"].get("content"):
                                chunk_content = chunk_data["choices"][0]["delta"]["content"]
                                full_response += chunk_content
                        except json.JSONDecodeError as e:
                            await context.error(f"JSONDecodeError processing stream chunk: {e} - Data: {data}")
                        except Exception as e:
                            await context.error(f"Error processing stream chunk: {e} - Data: {data}")
        await context.report_progress(progress=2, total=2, message="LLM stream completed.")
    except aiohttp.ClientError as e:
        await context.error(f"AIOHTTP ClientError in stream_chat: {e}")
        raise ToolError(f"Error connecting to Chutes API: {e}")
    except Exception as e:
        await context.error(f"Unexpected error in stream_chat: {e}")
        raise ToolError(f"An unexpected error occurred: {e}")
    
    await context.info("Exiting stream_chat function with successful response.")
    return full_response

@mcp.tool(
    name="chutes_chat",
    description="Sends a prompt to a Chutes LLM and gets a single response. Use this for non-streaming applications.",
    annotations={
        "title": "Chutes Chat",
        "readOnlyHint": True,  # It reads from LLM, doesn't modify environment
        "openWorldHint": True   # It interacts with an external LLM API
    }
)
async def chat( # Changed to async def
    context: Context,
    messages: Annotated[List[Dict[str, str]], Field(description="A list of message objects, each with a 'role' (e.g., 'user', 'assistant') and 'content' string. Represents the conversation history.")],
    model: Annotated[str, Field(description="The model to use for the completion.")] = config.get("chutes.models.llm"),
    temperature: Annotated[float, Field(description="The sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.", ge=0.0, le=2.0)] = 0.7,
    max_tokens: Annotated[int, Field(description="The maximum number of tokens to generate in the chat completion. The token count of your prompt plus max_tokens cannot exceed the model's context length.", ge=1)] = 1024,
) -> str:
    """
    Sends a chat message to the Chutes LLM endpoint and gets a single response.

    :param messages: A list of messages in the conversation.
    :param model: The model to use for the completion.
    :param temperature: The temperature for the completion.
    :param max_tokens: The maximum number of tokens to generate.
    :return: The content of the response from the LLM.
    """
    await context.info("Entering chat function.")
    await context.debug(f"Chat Parameters: model={model}, temperature={temperature}, max_tokens={max_tokens}")

    api_token = config.get("chutes.api_token")
    if not api_token:
        await context.warning("CHUTES_API_TOKEN environment variable not set for chat.")
        raise ToolError("CHUTES_API_TOKEN environment variable not set.")

    llm_endpoint = config.get("chutes.endpoints.llm")
    if not llm_endpoint:
        await context.warning("LLM endpoint not configured in config.yaml for chat.")
        raise ToolError("LLM endpoint not configured in config.yaml.")

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
        await context.report_progress(progress=0, total=2, message="Preparing LLM request.")
        async with aiohttp.ClientSession() as session: # Changed to aiohttp
            await context.report_progress(progress=1, total=2, message="Sending request to LLM API...")
            async with session.post( # Changed to aiohttp
                llm_endpoint,
                headers=headers,
                json=body
            ) as response:
                response.raise_for_status()
                response_data = await response.json() # Changed to await response.json()
        await context.report_progress(progress=2, total=2, message="Received response from LLM API.")
        await context.info("Chat function successfully received response.")
        await context.debug(f"Chat response data: {response_data}")
        return response_data["choices"][0]["message"]["content"]
    except aiohttp.ClientError as e: # Changed exception type
        await context.error(f"AIOHTTP ClientError in chat function: {e}")
        raise ToolError(f"Error connecting to Chutes API: {e}")
    except (KeyError, IndexError) as e:
        await context.error(f"Error parsing response from Chutes API in chat function: {e} - Response: {response_data if 'response_data' in locals() else 'N/A'}")
        raise ToolError(f"Error parsing response from Chutes API: {e} - Response: {response_data if 'response_data' in locals() else 'N/A'}")
    except Exception as e:
        await context.error(f"Unexpected error in chat function: {e}")
        raise ToolError(f"An unexpected error occurred: {e}")
