import os
import requests
import uuid
from typing import Optional, Union
from src.mcp_instance import mcp
from src.config import config
from fastmcp.utilities.types import Audio
from src.utils.imagekit_uploader import upload_to_imagekit

@mcp.tool(
    name="generate_music",
    description="Generates a music file. By default, it uploads the file to ImageKit as a side effect."
)
def generate_music(
    style_prompt: Optional[str] = None,
    lyrics: Optional[str] = None,
    audio_b64: Optional[str] = None,
    save_to_file: bool = True,
) -> Union[Audio, str]:
    """
    Generates music using the Chutes music generation API.

    :param style_prompt: A description of the desired music style.
    :param lyrics: The lyrics for the song.
    :param audio_b64: A base64 encoded audio file to be used as input.
    :param save_to_file: If True, uploads the audio to ImageKit as a side effect.
    :return: An Audio object on success, or an error message string.
    """
    api_token = config.get("chutes.api_token")
    if not api_token:
        return "Error: CHUTES_API_TOKEN environment variable not set."

    music_endpoint = config.get("chutes.endpoints.music")
    if not music_endpoint:
        return "Error: Music endpoint not configured in config.yaml."

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
        response = requests.post(
            music_endpoint,
            headers=headers,
            json=body
        )
        response.raise_for_status()
        audio_data = response.content

        url = None
        if save_to_file:
            metadata = {
                "style_prompt": style_prompt,
                "lyrics": lyrics,
            }
            url = upload_to_imagekit(audio_data, "generated_music", metadata, "wav")
        
        return Audio(data=audio_data, format="wav", annotations={"imagekit_url": url} if url else None)

    except requests.exceptions.RequestException as e:
        return f"Error calling Chutes Music API: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
