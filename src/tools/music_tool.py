import os
import requests
import uuid
from typing import Optional
from src.app import mcp

@mcp.tool(
    name="generate_music",
    description="Generates a music file based on a style prompt, lyrics, or an input audio file."
)
def generate_music(
    style_prompt: Optional[str] = None,
    lyrics: Optional[str] = None,
    audio_b64: Optional[str] = None,
) -> str:
    """
    Generates music using the Chutes music generation API.

    :param style_prompt: A description of the desired music style.
    :param lyrics: The lyrics for the song.
    :param audio_b64: A base64 encoded audio file to be used as input.
    :return: The path to the saved audio file, or an error message.
    """
    api_token = os.getenv("CHUTES_API_TOKEN")
    if not api_token:
        return "Error: CHUTES_API_TOKEN environment variable not set."

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
            "https://chutes-diffrhythm.chutes.ai/generate",
            headers=headers,
            json=body
        )
        response.raise_for_status()
        audio_data = response.content

        # Ensure the instance_data directory exists
        if not os.path.exists("instance_data"):
            os.makedirs("instance_data")

        # Generate a unique filename
        filename = f"instance_data/{uuid.uuid4()}.wav"
        
        # Save the audio
        with open(filename, "wb") as f:
            f.write(audio_data)
        
        return f"Music saved to {filename}"

    except requests.exceptions.RequestException as e:
        return f"Error calling Chutes Music API: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
