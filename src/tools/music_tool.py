import os
import aiohttp
from loguru import logger
import requests
import uuid
from typing import Optional, Union, Annotated
from fastmcp.exceptions import ToolError
from src.mcp_instance import mcp
from src.config import config
from fastmcp.utilities.types import Audio
from src.utils.imagekit_uploader import upload_to_imagekit
from pydantic import Field

@mcp.tool(
    name="generate_music",
    description="Generates a music file. By default, it uploads the file to ImageKit as a side effect.",
    annotations={
        "title": "Generate Music",
        "readOnlyHint": False,  # Because it uploads the file
        "openWorldHint": True   # Because it calls an external API
    }
)
async def generate_music( # Changed to async def
    style_prompt: Annotated[Optional[str], Field(description="A description of the desired music style, e.g., 'lo-fi beat', 'classical piano', 'rock anthem'.")] = None,
    lyrics: Annotated[Optional[str], Field(description="The lyrics for the song. If provided, the music will be generated to match these lyrics.")] = None,
    audio_b64: Annotated[Optional[str], Field(description="A base64 encoded audio file to be used as input for music generation or transformation.")] = None,
    save_to_file: Annotated[bool, Field(description="If True, uploads the generated audio to ImageKit for persistent storage and URL access.")] = True,
) -> Union[Audio, str]:
    """
    Generates music using the Chutes music generation API.

    :param style_prompt: A description of the desired music style.
    :param lyrics: The lyrics for the song.
    :param audio_b64: A base64 encoded audio file to be used as input.
    :param save_to_file: If True, uploads the audio to ImageKit as a side effect.
    :return: An Audio object on success, or an error message string.
    """
    logger.info("Entering generate_music function.")
    logger.debug(f"Generate Music Parameters: style_prompt='{style_prompt}', lyrics='{lyrics}', audio_b64={'<present>' if audio_b64 else '<absent>'}, save_to_file={save_to_file}")

    api_token = config.get("chutes.api_token")
    if not api_token:
        logger.warning("CHUTES_API_TOKEN environment variable not set for generate_music.")
        raise ToolError("CHUTES_API_TOKEN environment variable not set.")

    music_endpoint = config.get("chutes.endpoints.text_to_music")
    if not music_endpoint:
        logger.warning("Text-to-music endpoint not configured in config.yaml for generate_music.")
        raise ToolError("Text-to-music endpoint not configured in config.yaml.")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    body = {
        "style_prompt": style_prompt,
        "lyrics": lyrics,
        "audio_b64": audio_b64,
    }

    try:
        logger.info(f"Calling Chutes Music API at {music_endpoint} for music generation.")
        async with aiohttp.ClientSession() as session: # Changed to aiohttp
            async with session.post( # Changed to aiohttp
                music_endpoint,
                headers=headers,
                json=body
            ) as response:
                response.raise_for_status()
                audio_data = await response.read() # Changed to await response.read()
        logger.info("Successfully received audio data from Chutes Music API.")

        url = None
        if save_to_file:
            logger.debug("Uploading generated music to ImageKit.")
            metadata = {
                "model": config.get("metadata.models.text_to_music"),
                "style_prompt": style_prompt,
                "lyrics": lyrics,
            }
            url = upload_to_imagekit(audio_data, "generated_music", metadata, "wav")
            if url:
                logger.info(f"Generated music uploaded to ImageKit: {url}")
            else:
                logger.error("Failed to upload generated music to ImageKit.")
        
        logger.info("Exiting generate_music function with successful response.")
        return Audio(data=audio_data, format="wav", annotations={"imagekit_url": url} if url else None)

    except aiohttp.ClientError as e: # Changed exception type
        logger.error(f"AIOHTTP ClientError calling Chutes Music API in generate_music: {e}")
        raise ToolError(f"Error calling Chutes Music API: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in generate_music: {e}", exc_info=True)
        raise ToolError(f"An unexpected error occurred: {e}")
