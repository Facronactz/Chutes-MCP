import os
import aiohttp
import requests
import uuid
from typing import Optional, List, Union
from src.mcp_instance import mcp
from src.config import config
from fastmcp.utilities.types import Image
from src.utils.imagekit_uploader import upload_to_imagekit

@mcp.tool(
    name="generate_image",
    description="Generates an image from a text prompt. By default, uploads the image to ImageKit as a side effect."
)
async def generate_image(
    prompt: str,
    negative_prompt: Optional[str] = None,
    width: int = 1024,
    height: int = 1024,
    num_inference_steps: int = 50,
    seed: Optional[int] = None,
    save_to_file: bool = True,
) -> Union[Image, str]:
    """
    Generates an image using the Chutes image generation API.

    :param prompt: A text description of the desired image.
    :param negative_prompt: A text description of what to avoid in the image.
    :param width: The width of the generated image.
    :param height: The height of the generated image.
    :param num_inference_steps: The number of denoising steps.
    :param seed: A seed for reproducible generation.
    :param save_to_file: If True, uploads the image to ImageKit as a side effect.
    :return: An Image object on success, or an error message string.
    """
    api_token = config.get("chutes.api_token")
    if not api_token:
        return "Error: CHUTES_API_TOKEN environment variable not set."

    image_endpoint = config.get("chutes.endpoints.image")
    if not image_endpoint:
        return "Error: Image endpoint not configured in config.yaml."

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    if negative_prompt is None:
        negative_prompt = ""

    body = {
        "model": "qwen-image",
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "num_inference_steps": num_inference_steps,
        "seed": seed,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                image_endpoint,
                headers=headers,
                json=body
            ) as response:
                response.raise_for_status()
                image_data = await response.read()
                
                url = None
                if save_to_file:
                    metadata = {
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "width": width,
                        "height": height,
                        "num_inference_steps": num_inference_steps,
                        "seed": seed,
                    }
                    url = upload_to_imagekit(image_data, "generated_image", metadata)
                
                return Image(data=image_data, format="jpeg", annotations={"imagekit_url": url} if url else None)

    except aiohttp.ClientError as e:
        return f"Error calling Chutes Image API: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@mcp.tool(
    name="edit_image",
    description="Edits an image based on a text prompt. By default, uploads the image to ImageKit as a side effect."
)
def edit_image(
    prompt: str,
    image_b64s: List[str],
    negative_prompt: Optional[str] = "",
    width: int = 1024,
    height: int = 1024,
    num_inference_steps: int = 40,
    seed: Optional[int] = None,
    true_cfg_scale: float = 4.0,
    save_to_file: bool = True,
) -> Union[Image, str]:
    """
    Edits an image using the Chutes image editing API.

    :param prompt: A text description of the desired edit.
    :param image_b64s: A list of base64 encoded images to be edited.
    :param negative_prompt: A text description of what to avoid in the image.
    :param width: The width of the generated image.
    :param height: The height of the generated image.
    :param num_inference_steps: The number of denoising steps.
    :param seed: A seed for reproducible generation.
    :param true_cfg_scale: A parameter to control how much the model should follow the prompt.
    :param save_to_file: If True, uploads the image to ImageKit as a side effect.
    :return: An Image object on success, or an error message string.
    """
    api_token = config.get("chutes.api_token")
    if not api_token:
        return "Error: CHUTES_API_TOKEN environment variable not set."

    image_edit_endpoint = config.get("chutes.endpoints.image_edit")
    if not image_edit_endpoint:
        return "Error: Image edit endpoint not configured in config.yaml."

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    body = {
        "prompt": prompt,
        "image_b64s": image_b64s,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "num_inference_steps": num_inference_steps,
        "seed": seed,
        "true_cfg_scale": true_cfg_scale,
    }

    try:
        response = requests.post(
            image_edit_endpoint,
            headers=headers,
            json=body
        )
        response.raise_for_status()
        image_data = response.content

        url = None
        if save_to_file:
            metadata = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_inference_steps": num_inference_steps,
                "seed": seed,
                "true_cfg_scale": true_cfg_scale,
            }
            url = upload_to_imagekit(image_data, "edited_image", metadata)
        
        return Image(data=image_data, format="jpeg", annotations={"imagekit_url": url} if url else None)

    except requests.exceptions.RequestException as e:
        return f"Error calling Chutes Image Edit API: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
