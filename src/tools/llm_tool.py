import os
import aiohttp
import json
from loguru import logger
import requests
from typing import List, Dict
from src.mcp_instance import mcp
from src.config import config

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
    logger.info("Entering stream_chat function.")
    logger.debug(f"Stream Chat Parameters: model={model}, temperature={temperature}, max_tokens={max_tokens}")

    api_token = config.get("chutes.api_token")
    if not api_token:
        logger.warning("CHUTES_API_TOKEN environment variable not set for stream_chat.")
        return "Error: CHUTES_API_TOKEN environment variable not set."

    llm_endpoint = config.get("chutes.endpoints.llm")
    if not llm_endpoint:
        logger.warning("LLM endpoint not configured in config.yaml for stream_chat.")
        return "Error: LLM endpoint not configured in config.yaml."

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
        async with aiohttp.ClientSession() as session:
            async with session.post(
                llm_endpoint,
                headers=headers,
                json=body
            ) as response:
                response.raise_for_status()  # Raise an exception for bad status codes
                logger.debug(f"Stream chat request sent to {llm_endpoint}, status: {response.status}")
                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            logger.debug("Stream finished with [DONE] signal.")
                            break
                        try:
                            chunk_data = json.loads(data)
                            if chunk_data["choices"][0]["delta"].get("content"):
                                chunk_content = chunk_data["choices"][0]["delta"]["content"]
                                full_response += chunk_content
                        except json.JSONDecodeError as e:
                            logger.error(f"JSONDecodeError processing stream chunk: {e} - Data: {data}")
                        except Exception as e:
                            logger.error(f"Error processing stream chunk: {e} - Data: {data}")
    except aiohttp.ClientError as e:
        logger.error(f"AIOHTTP ClientError in stream_chat: {e}")
        return f"Error connecting to Chutes API: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in stream_chat: {e}")
        return f"An unexpected error occurred: {e}"
    
    logger.info("Exiting stream_chat function with successful response.")
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
    logger.info("Entering chat function.")
    logger.debug(f"Chat Parameters: model={model}, temperature={temperature}, max_tokens={max_tokens}")

    api_token = config.get("chutes.api_token")
    if not api_token:
        logger.warning("CHUTES_API_TOKEN environment variable not set for chat.")
        return "Error: CHUTES_API_TOKEN environment variable not set."

    llm_endpoint = config.get("chutes.endpoints.llm")
    if not llm_endpoint:
        logger.warning("LLM endpoint not configured in config.yaml for chat.")
        return "Error: LLM endpoint not configured in config.yaml."

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
            llm_endpoint,
            headers=headers,
            json=body
        )
        response.raise_for_status()
        response_data = response.json()
        logger.info("Chat function successfully received response.")
        logger.debug(f"Chat response data: {response_data}")
        return response_data["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Chutes API in chat function: {e}")
        return f"Error calling Chutes API: {e}"
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing response from Chutes API in chat function: {e} - Response: {response.text if 'response' in locals() else 'N/A'}")
        return f"Error parsing response from Chutes API: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in chat function: {e}")
        return f"An unexpected error occurred: {e}"
