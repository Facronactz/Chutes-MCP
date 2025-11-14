import os
import requests
import uuid
from typing import Optional
from src.app import mcp
from src.config import config

@mcp.tool(
    name="generate_video_from_text",
    description="Generates a video based on a text prompt and saves it to a file."
)
def generate_video_from_text(
    prompt: str,
    negative_prompt: Optional[str] = "Vibrant colors, overexposed, static, blurry details, subtitles, style, artwork, painting, picture, still, overall grayish, worst quality, low quality, JPEG compression artifacts, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn face, deformed, disfigured, malformed limbs, fused fingers, motionless image, cluttered background, three legs, many people in the background, walking backwards, slow motion",
    resolution: str = "832*480",
    fps: int = 24,
    frames: int = 81,
    steps: int = 25,
    guidance_scale: float = 5.0,
    seed: Optional[int] = 42,
) -> str:
    """
    Generates a video using the Chutes text-to-video generation API.

    :param prompt: A text description of the desired video.
    :param negative_prompt: A text description of what to avoid in the video.
    :param resolution: The resolution of the video.
    :param fps: The frames per second of the video.
    :param frames: The number of frames to generate.
    :param steps: The number of denoising steps.
    :param guidance_scale: A parameter to control how much the model should follow the prompt.
    :param seed: A seed for reproducible generation.
    :return: The path to the saved video, or an error message.
    """
    api_token = config.get("chutes.api_token")
    if not api_token:
        return "Error: CHUTES_API_TOKEN environment variable not set."

    video_endpoint = config.get("chutes.endpoints.text_to_video")
    if not video_endpoint:
        return "Error: Text-to-video endpoint not configured in config.yaml."

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    body = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "resolution": resolution,
        "fps": fps,
        "frames": frames,
        "steps": steps,
        "guidance_scale": guidance_scale,
        "seed": seed,
    }

    try:
        response = requests.post(
            video_endpoint,
            headers=headers,
            json=body
        )
        response.raise_for_status()
        video_data = response.content

        if not os.path.exists("instance_data"):
            os.makedirs("instance_data")

        filename = f"instance_data/{uuid.uuid4()}.mp4"
        
        with open(filename, "wb") as f:
            f.write(video_data)
        
        return f"Video saved to {filename}"

    except requests.exceptions.RequestException as e:
        return f"Error calling Chutes Text-to-Video API: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@mcp.tool(
    name="generate_video_from_image",
    description="Generates a video based on an image and a text prompt, and saves it to a file."
)
def generate_video_from_image(
    prompt: str,
    image_b64: str,
    negative_prompt: Optional[str] = "Vibrant colors, overexposed, static, blurry details, subtitles, style, artwork, painting, picture, still, overall grayish, worst quality, low quality, JPEG compression artifacts, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn face, deformed, disfigured, malformed limbs, fused fingers, motionless image, cluttered background, three legs, many people in the background, walking backwards, slow motion",
    steps: int = 25,
    guidance_scale: float = 5.0,
    seed: Optional[int] = 42,
) -> str:
    """
    Generates a video using the Chutes image-to-video generation API.

    :param prompt: A text description of the desired video.
    :param image_b64: A base64 encoded image to use as the starting point.
    :param negative_prompt: A text description of what to avoid in the video.
    :param steps: The number of denoising steps.
    :param guidance_scale: A parameter to control how much the model should follow the prompt.
    :param seed: A seed for reproducible generation.
    :return: The path to the saved video, or an error message.
    """
    api_token = config.get("chutes.api_token")
    if not api_token:
        return "Error: CHUTES_API_TOKEN environment variable not set."

    video_endpoint = config.get("chutes.endpoints.image_to_video")
    if not video_endpoint:
        return "Error: Image-to-video endpoint not configured in config.yaml."

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    body = {
        "prompt": prompt,
        "image_b64": image_b64,
        "negative_prompt": negative_prompt,
        "steps": steps,
        "guidance_scale": guidance_scale,
        "seed": seed,
    }

    try:
        response = requests.post(
            video_endpoint,
            headers=headers,
            json=body
        )
        response.raise_for_status()
        video_data = response.content

        if not os.path.exists("instance_data"):
            os.makedirs("instance_data")

        filename = f"instance_data/{uuid.uuid4()}.mp4"
        
        with open(filename, "wb") as f:
            f.write(video_data)
        
        return f"Video saved to {filename}"

    except requests.exceptions.RequestException as e:
        return f"Error calling Chutes Image-to-Video API: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
