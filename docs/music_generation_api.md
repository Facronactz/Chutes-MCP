### Chutes Music Generation API Documentation

This document outlines the schema for the Chutes music generation endpoint.

#### Endpoint Overview

*   **Public Path:** `/generate`
*   **URL:** `https://chutes-diffrhythm.chutes.ai/generate`
*   **Method:** `POST`
*   **Authentication:** Requests must be authenticated using a Bearer token in the `Authorization` header.
    *   Example: `Authorization: Bearer YOUR_CHUTES_API_TOKEN`

---

#### Input Schema (`InputArgs`)

The body of your `POST` request should be a JSON object that conforms to the `InputArgs` schema.

##### Properties:

*   `lyrics` (string, optional): The lyrics for the song.
*   `style_prompt` (string, optional): A description of the desired music style.
*   `audio_b64` (string, optional): A base64 encoded audio file to be used as input.

---

#### Output

*   **Content-Type:** `audio/wav`
*   The response body will be the raw audio data.

---

#### Examples

Here are some examples of how to call the endpoint.

##### `curl`

```bash
curl -X POST \
    https://chutes-diffrhythm.chutes.ai/generate \
    -H "Authorization: Bearer $CHUTES_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "lyrics": null,
        "style_prompt": null
    }'
```

##### Python (`requests`)

```python
import requests

def invoke_chute():
    api_token = "$CHUTES_API_TOKEN"  # Replace with your actual API token

    headers = {
        "Authorization": "Bearer " + api_token,
        "Content-Type": "application/json"
    }
    
    body = {
      "style_prompt": null
    }

    response = requests.post(
        "https://chutes-diffrhythm.chutes.ai/generate",
        headers=headers,
        json=body
    )

    # The response content will be the audio bytes
    # You can save it to a file like this:
    if response.status_code == 200:
        with open("generated_music.wav", "wb") as f:
            f.write(response.content)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


invoke_chute()
```
