import aiohttp
from loguru import logger
import requests
import uuid
from typing import Optional, Union, Annotated
from fastmcp.exceptions import ToolError
from src.mcp_instance import mcp
from src.config import config
from fastmcp.utilities.types import File
from src.utils.imagekit_uploader import upload_to_imagekit
from pydantic import Field

@mcp.tool(
    name="generate_video_from_text",
    description="Generates a video from a text prompt. By default, uploads the video to ImageKit as a side effect.",
    annotations={
        "title": "Generate Video from Text",
        "readOnlyHint": False,  # Because it uploads the video
        "openWorldHint": True   # Because it calls an external API
    }
)
async def generate_video_from_text( # Changed to async def
    prompt: Annotated[str, Field(description="A text description of the desired video to generate.")],
    negative_prompt: Annotated[Optional[str], Field(description="A text description of what to avoid in the video.")] = "Vibrant colors, overexposed, static, blurry details, subtitles, style, artwork, painting, picture, still, overall grayish, worst quality, low quality, JPEG compression artifacts, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn face, deformed, disfigured, malformed limbs, fused fingers, motionless image, cluttered background, three legs, many people in the background, walking backwards, slow motion",
    resolution: Annotated[str, Field(description="The resolution of the video (e.g., '832*480', '1024*576').")] = "832*480",
    fps: Annotated[int, Field(description="The frames per second of the video.", ge=1, le=60)] = 24,
    frames: Annotated[int, Field(description="The number of frames to generate for the video.", ge=1)] = 81,
    steps: Annotated[int, Field(description="The number of denoising steps.", ge=1, le=100)] = 25,
    guidance_scale: Annotated[float, Field(description="A parameter to control how much the model should follow the prompt.", ge=1.0, le=20.0)] = 5.0,
    seed: Annotated[Optional[int], Field(description="A seed for reproducible generation. If None, a random seed is used.")] = 42,
    save_to_file: Annotated[bool, Field(description="If True, uploads the generated video to ImageKit for persistent storage and URL access.")] = True,
) -> Union[File, str]:
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
    :param save_to_file: If True, uploads the video to ImageKit as a side effect.
    :return: A File object on success, or an error message string.
    """
    logger.info("Entering generate_video_from_text function.")
    logger.debug(f"Generate Video from Text Parameters: prompt='{prompt}', negative_prompt='{negative_prompt}', resolution='{resolution}', fps={fps}, frames={frames}, steps={steps}, guidance_scale={guidance_scale}, seed={seed}, save_to_file={save_to_file}")

    api_token = config.get("chutes.api_token")
    if not api_token:
        logger.warning("CHUTES_API_TOKEN environment variable not set for generate_video_from_text.")
        raise ToolError("CHUTES_API_TOKEN environment variable not set.")

    video_endpoint = config.get("chutes.endpoints.text_to_video")
    if not video_endpoint:
        logger.warning("Text-to-video endpoint not configured in config.yaml for generate_video_from_text.")
        raise ToolError("Text-to-video endpoint not configured in config.yaml.")

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
        logger.info(f"Calling Chutes Text-to-Video API at {video_endpoint} for video generation.")
        async with aiohttp.ClientSession() as session: # Changed to aiohttp
            async with session.post( # Changed to aiohttp
                video_endpoint,
                headers=headers,
                json=body
            ) as response:
                response.raise_for_status()
                video_data = await response.read() # Changed to await response.read()
        logger.info("Successfully received video data from Chutes Text-to-Video API.")

        url = None
        if save_to_file:
            logger.debug("Uploading generated video to ImageKit.")
            metadata = {
                "model": config.get("metadata.models.text_to_video"),
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "resolution": resolution,
                "fps": fps,
                "frames": frames,
                "steps": steps,
                "guidance_scale": guidance_scale,
                "seed": seed,
            }
            url = upload_to_imagekit(video_data, "generated_video_from_text", metadata, "mp4")
            if url:
                logger.info(f"Generated video uploaded to ImageKit: {url}")
            else:
                logger.error("Failed to upload generated video to ImageKit.")
        
        logger.info("Exiting generate_video_from_text function with successful response.")
        return File(data=video_data, format="mp4", annotations={"imagekit_url": url} if url else None)

    except aiohttp.ClientError as e: # Changed exception type
        logger.error(f"AIOHTTP ClientError calling Chutes Text-to-Video API in generate_video_from_text: {e}")
        raise ToolError(f"Error calling Chutes Text-to-Video API: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in generate_video_from_text: {e}", exc_info=True)
        raise ToolError(f"An unexpected error occurred: {e}")

@mcp.tool(
    name="generate_video_from_image",
    description="Generates a video from an image and prompt. By default, uploads the video to ImageKit as a side effect.",
    annotations={
        "title": "Generate Video from Image",
        "readOnlyHint": False,  # Because it uploads the video
        "openWorldHint": True   # Because it calls an external API
    }
)
async def generate_video_from_image( # Changed to async def
    prompt: Annotated[str, Field(description="A text description of the desired video to generate.")],
    image_b64: Annotated[str, Field(description="A base64 encoded image to use as the starting point for video generation.")],
    negative_prompt: Annotated[Optional[str], Field(description="A text description of what to avoid in the video.")] = "Vibrant colors, overexposed, static, blurry details, subtitles, style, artwork, painting, picture, still, overall grayish, worst quality, low quality, JPEG compression artifacts, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn face, deformed, disfigured, malformed limbs, fused fingers, motionless image, cluttered background, three legs, many people in the background, walking backwards, slow motion",
    steps: Annotated[int, Field(description="The number of denoising steps.", ge=1, le=100)] = 25,
    guidance_scale: Annotated[float, Field(description="A parameter to control how much the model should follow the prompt.", ge=1.0, le=20.0)] = 5.0,
    seed: Annotated[Optional[int], Field(description="A seed for reproducible generation. If None, a random seed is used.")] = 42,
    save_to_file: Annotated[bool, Field(description="If True, uploads the generated video to ImageKit for persistent storage and URL access.")] = True,
) -> Union[File, str]:
    """
    Generates a video using the Chutes image-to-video generation API.

    :param prompt: A text description of the desired video.
    :param image_b64: A base64 encoded image to use as the starting point.
    :param negative_prompt: A text description of what to avoid in the video.
    :param steps: The number of denoising steps.
    :param guidance_scale: A parameter to control how much the model should follow the prompt.
    :param seed: A seed for reproducible generation.
    :param save_to_file: If True, uploads the video to ImageKit as a side effect.
    :return: A File object on success, or an error message string.
    """
    logger.info("Entering generate_video_from_image function.")
    logger.debug(f"Generate Video from Image Parameters: prompt='{prompt}', image_b64={'<present>' if image_b64 else '<absent>'}, negative_prompt='{negative_prompt}', steps={steps}, guidance_scale={guidance_scale}, seed={seed}, save_to_file={save_to_file}")

    api_token = config.get("chutes.api_token")
    if not api_token:
        logger.warning("CHUTES_API_TOKEN environment variable not set for generate_video_from_image.")
        raise ToolError("CHUTES_API_TOKEN environment variable not set.")

    video_endpoint = config.get("chutes.endpoints.image_to_video")
    if not video_endpoint:
        logger.warning("Image-to-video endpoint not configured in config.yaml for generate_video_from_image.")
        raise ToolError("Image-to-video endpoint not configured in config.yaml.")

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
        logger.info(f"Calling Chutes Image-to-Video API at {video_endpoint} for video generation.")
        async with aiohttp.ClientSession() as session: # Changed to aiohttp
            async with session.post( # Changed to aiohttp
                video_endpoint,
                headers=headers,
                json=body
            ) as response:
                response.raise_for_status()
                video_data = await response.read() # Changed to await response.read()
        logger.info("Successfully received video data from Chutes Image-to-Video API.")

        url = None
        if save_to_file:
            logger.debug("Uploading generated video to ImageKit.")
            metadata = {
                "model": config.get("metadata.models.image_to_video"),
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "steps": steps,
                "guidance_scale": guidance_scale,
                "seed": seed,
            }
            url = upload_to_imagekit(video_data, "generated_video_from_image", metadata, "mp4")
            if url:
                logger.info(f"Generated video uploaded to ImageKit: {url}")
            else:
                logger.error("Failed to upload generated video to ImageKit.")
        
        logger.info("Exiting generate_video_from_image function with successful response.")
        return File(data=video_data, format="mp4", annotations={"imagekit_url": url} if url else None)

    except aiohttp.ClientError as e: # Changed exception type
        logger.error(f"AIOHTTP ClientError calling Chutes Image-to-Video API in generate_video_from_image: {e}")
        raise ToolError(f"Error calling Chutes Image-to-Video API: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in generate_video_from_image: {e}", exc_info=True)
        raise ToolError(f"An unexpected error occurred: {e}")
@mcp.tool(
    name="generate_video_from_image_fast",
    description="Generates a video from an image using a fast model. By default, uploads the video to ImageKit as a side effect.",
    annotations={
        "title": "Generate Video from Image (Fast)",
        "readOnlyHint": False,  # Because it uploads the video
        "openWorldHint": True   # Because it calls an external API
    }
)
async def generate_video_from_image_fast( # Changed to async def
    prompt: Annotated[str, Field(description="A text description of the desired video to generate.")],
    image: Annotated[str, Field(description="Image URL or base64 encoded data to use as the starting point for video generation.")],
    negative_prompt: Annotated[Optional[str], Field(description="A text description of what to avoid in the video.")] = "Vibrant colors, overexposed, static, blurry details, subtitles, style, artwork, painting, picture, still, overall grayish, worst quality, low quality, JPEG compression artifacts, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn face, deformed, disfigured, malformed limbs, fused fingers, motionless image, cluttered background, three legs, many people in the background, walking backwards, slow motion",
    fps: Annotated[int, Field(description="The frames per second of the video.", ge=1, le=60)] = 16,
    frames: Annotated[int, Field(description="The number of frames to generate for the video.", ge=1)] = 81,
    guidance_scale: Annotated[float, Field(description="A parameter to control how much the model should follow the prompt.", ge=1.0, le=20.0)] = 1.0,
    guidance_scale_2: Annotated[float, Field(description="A second guidance scale parameter for fine-tuning.", ge=1.0, le=20.0)] = 1.0,
    seed: Annotated[Optional[int], Field(description="A seed for reproducible generation. If None, a random seed is used.")] = None,
    fast: Annotated[bool, Field(description="Enables ultra fast Pruna mode for quicker generation.")] = True,
    resolution: Annotated[str, Field(description="The resolution of the video (e.g., '480p', '720p', '1080p').")] = "480p",
    save_to_file: Annotated[bool, Field(description="If True, uploads the generated video to ImageKit for persistent storage and URL access.")] = True,
) -> Union[File, str]:
    """
    Generates a video from an image using the fast Chutes image-to-video API.

    :param prompt: A text description of the desired video.
    :param image: Image URL or base64 encoded data.
    :param negative_prompt: A text description of what to avoid in the video.
    :param fps: The frames per second of the video.
    :param frames: The number of frames to generate.
    :param guidance_scale: A parameter to control how much the model should follow the prompt.
    :param guidance_scale_2: A second guidance scale parameter.
    :param seed: A seed for reproducible generation.
    :param fast: Enables ultra fast pruna mode.
    :param resolution: The resolution of the video.
    :param save_to_file: If True, uploads the video to ImageKit as a side effect.
    :return: A File object on success, or an error message string.
    """
    logger.info("Entering generate_video_from_image_fast function.")
    logger.debug(f"Generate Video from Image Fast Parameters: prompt='{prompt}', image={'<present>' if image else '<absent>'}, negative_prompt='{negative_prompt}', fps={fps}, frames={frames}, guidance_scale={guidance_scale}, guidance_scale_2={guidance_scale_2}, seed={seed}, fast={fast}, resolution='{resolution}', save_to_file={save_to_file}")

    api_token = config.get("chutes.api_token")
    if not api_token:
        logger.warning("CHUTES_API_TOKEN environment variable not set for generate_video_from_image_fast.")
        raise ToolError("CHUTES_API_TOKEN environment variable not set.")

    video_endpoint = config.get("chutes.endpoints.image_to_video_fast")
    if not video_endpoint:
        logger.warning("Fast image-to-video endpoint not configured in config.yaml for generate_video_from_image_fast.")
        raise ToolError("Fast image-to-video endpoint not configured in config.yaml.")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    body = {
        "prompt": prompt,
        "image": image,
        "negative_prompt": negative_prompt,
        "fps": fps,
        "frames": frames,
        "guidance_scale": guidance_scale,
        "guidance_scale_2": guidance_scale_2,
        "seed": seed,
        "fast": fast,
        "resolution": resolution,
    }

    try:
        logger.info(f"Calling Chutes Fast Image-to-Video API at {video_endpoint} for video generation.")
        async with aiohttp.ClientSession() as session: # Changed to aiohttp
            async with session.post( # Changed to aiohttp
                video_endpoint,
                headers=headers,
                json=body
            ) as response:
                response.raise_for_status()
                video_data = await response.read() # Changed to await response.read()
        logger.info("Successfully received video data from Chutes Fast Image-to-Video API.")

        url = None
        if save_to_file:
            logger.debug("Uploading generated video to ImageKit.")
            metadata = {
                "model": config.get("metadata.models.image_to_video_fast"),
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "fps": fps,
                "frames": frames,
                "guidance_scale": guidance_scale,
                "guidance_scale_2": guidance_scale_2,
                "seed": seed,
                "fast": fast,
                "resolution": resolution,
            }
            url = upload_to_imagekit(video_data, "generated_video_from_image_fast", metadata, "mp4")
            if url:
                logger.info(f"Generated video uploaded to ImageKit: {url}")
            else:
                logger.error("Failed to upload generated video to ImageKit.")
        
        logger.info("Exiting generate_video_from_image_fast function with successful response.")
        return File(data=video_data, format="mp4", annotations={"imagekit_url": url} if url else None)

    except aiohttp.ClientError as e: # Changed exception type
        logger.error(f"AIOHTTP ClientError calling Chutes Fast Image-to-Video API in generate_video_from_image_fast: {e}")
        raise ToolError(f"Error calling Chutes Fast Image-to-Video API: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in generate_video_from_image_fast: {e}", exc_info=True)
        raise ToolError(f"An unexpected error occurred: {e}")
