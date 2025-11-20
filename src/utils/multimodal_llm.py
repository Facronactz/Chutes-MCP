import os
import base64
from typing import List, Dict, Union
import aiohttp
from loguru import logger
from fastmcp.exceptions import ToolError
from src.config import config

class MultimodalLLM:
    def __init__(self):
        self.api_token = config.get("chutes.api_token")
        if not self.api_token:
            logger.warning("CHUTES_API_TOKEN environment variable not set for MultimodalLLM.")
            raise ToolError("CHUTES_API_TOKEN environment variable not set.")
        
        self.llm_endpoint = config.get("chutes.endpoints.llm")
        if not self.llm_endpoint:
            logger.warning("LLM endpoint not configured in config.yaml for MultimodalLLM.")
            raise ToolError("LLM endpoint not configured in config.yaml.")

        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    async def ask_with_images(self, prompt: str, images: List[Union[str, bytes]], model: str = None, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        logger.info("Entering MultimodalLLM.ask_with_images function.")
        
        # Ensure model is set, default to config if not provided
        if model is None:
            model = config.get("chutes.models.vision_llm")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        for img in images:
            if isinstance(img, bytes):
                # Assume bytes are raw image data, base64 encode them
                base64_image = base64.b64encode(img).decode("utf-8")
                messages[0]["content"].append(
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                )
            elif isinstance(img, str) and (img.startswith("http") or img.startswith("data:image")):
                # Assume string is a URL or data URI
                messages[0]["content"].append(
                    {"type": "image_url", "image_url": {"url": img}}
                )
            else:
                logger.warning(f"Unsupported image format or type: {type(img)}. Skipping image.")
                continue

        body = {
            "model": model,
            "messages": messages,
            "stream": False,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            logger.debug(f"Calling Chutes LLM API at {self.llm_endpoint} for multimodal request.")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.llm_endpoint,
                    headers=self.headers,
                    json=body
                ) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    logger.info("Multimodal LLM request successful.")
                    return response_data["choices"][0]["message"]["content"]
        except aiohttp.ClientError as e:
            logger.error(f"AIOHTTP ClientError calling Chutes LLM API in ask_with_images: {e}")
            raise ToolError(f"Error calling Chutes LLM API: {e}")
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing response from Chutes LLM API in ask_with_images: {e} - Response: {response_data if 'response_data' in locals() else 'N/A'}")
            raise ToolError(f"Error parsing response from Chutes LLM API: {e} - Response: {response_data if 'response_data' in locals() else 'N/A'}")
        except Exception as e:
            logger.error(f"An unexpected error occurred in ask_with_images: {e}", exc_info=True)
            raise ToolError(f"An unexpected error occurred: {e}")

