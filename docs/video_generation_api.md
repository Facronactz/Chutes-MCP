### Chutes Video Generation API Documentation

This document outlines the schemas for the Chutes video generation endpoints.

---

### Text-to-Video

#### Endpoint Overview

*   **Public Path:** `/text2video`
*   **URL:** `https://chutes-wan2-1-14b.chutes.ai/text2video`
*   **Method:** `POST`
*   **Authentication:** Requests must be authenticated using a Bearer token in the `Authorization` header.
    *   Example: `Authorization: Bearer YOUR_CHUTES_API_TOKEN`

---

#### Input Schema (`VideoGenInput`)

The body of your `POST` request should be a JSON object that conforms to the `VideoGenInput` schema.

##### Required Properties:

*   `prompt` (string): A text description of the desired video.

##### Optional Properties:

*   `negative_prompt` (string): A text description of what to avoid in the video.
*   `resolution` (string, default: "832*480"): The resolution of the video.
*   `fps` (integer, default: 24): The frames per second of the video.
*   `frames` (integer, default: 81): The number of frames to generate.
*   `steps` (integer, default: 25): The number of denoising steps.
*   `guidance_scale` (number, default: 5): A parameter to control how much the model should follow the prompt.
*   `seed` (integer, default: 42): A seed for reproducible generation.

---

### Image-to-Video

#### Endpoint Overview

*   **Public Path:** `/image2video`
*   **URL:** `https://chutes-wan2-1-14b.chutes.ai/image2video`
*   **Method:** `POST`
*   **Authentication:** Requests must be authenticated using a Bearer token in the `Authorization` header.

---

#### Input Schema (`I2VInput`)

##### Required Properties:

*   `prompt` (string): A text description of the desired video.
*   `image_b64` (string): A base64 encoded image to use as the starting point.

##### Optional Properties:

*   This endpoint shares the same optional properties as the text-to-video endpoint (`negative_prompt`, `resolution`, `fps`, etc.).

---

#### Output (for both endpoints)

*   **Content-Type:** `video/mp4`
*   The response body will be the raw video data.

---

#### Examples

##### `curl` (Text-to-Video)

```bash
curl -X POST \
    https://chutes-wan2-1-14b.chutes.ai/text2video \
    -H "Authorization: Bearer $CHUTES_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "fps": 24,
        "steps": 25,
        "frames": 81,
        "prompt": "example-string",
        "resolution": "832*480",
        "sample_shift": null,
        "guidance_scale": 5
    }'
```

##### `curl` (Image-to-Video)

```bash
curl -X POST \
    https://chutes-wan2-1-14b.chutes.ai/image2video \
    -H "Authorization: Bearer $CHUTES_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "steps": 25,
        "frames": 81,
        "prompt": "example-string",
        "image_b64": "example-string",
        "sample_shift": null
    }'
```

##### Python (`requests`) (Image-to-Video)

```python
import requests

def invoke_chute():
    api_token = "$CHUTES_API_TOKEN"  # Replace with your actual API token

    headers = {
        "Authorization": "Bearer " + api_token,
        "Content-Type": "application/json"
    }
    
    body = {
      "seed": 42,
      "steps": 25,
      "prompt": "example-string",
      "image_b64": "example-string",
      "sample_shift": null,
      "single_frame": False,
      "guidance_scale": 5
    }

    response = requests.post(
        "https://chutes-wan2-1-14b.chutes.ai/image2video",
        headers=headers,
        json=body
    )

    # The response content will be the video bytes
    # You can save it to a file like this:
    if response.status_code == 200:
        with open("generated_video.mp4", "wb") as f:
            f.write(response.content)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

invoke_chute()
```