import os
import aiohttp
import uuid
from typing import Optional
from src.app import mcp
from src.config import config

@mcp.tool(
    name="generate_image",
    description="Generates an image based on a text prompt and saves it to a file."
)
async def generate_image(
    prompt: str,
    negative_prompt: Optional[str] = None,
    width: int = 1024,
    height: int = 1024,
    num_inference_steps: int = 50,
    seed: Optional[int] = None,
) -> str:
    """
    Generates an image using the Chutes image generation API.

    :param prompt: A text description of the desired image.
    :param negative_prompt: A text description of what to avoid in the image.
    :param width: The width of the generated image.
    :param height: The height of the generated image.
    :param num_inference_steps: The number of denoising steps.
    :param seed: A seed for reproducible generation.
    :return: The path to the saved image, or an error message.
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

                # Ensure the instance_data directory exists
                if not os.path.exists("instance_data"):
                    os.makedirs("instance_data")

                # Generate a unique filename
                filename = f"instance_data/{uuid.uuid4()}.jpg"
                
                # Save the image
                with open(filename, "wb") as f:
                    f.write(image_data)
                
                return f"Image saved to {filename}"

    except aiohttp.ClientError as e:
        return f"Error calling Chutes Image API: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
