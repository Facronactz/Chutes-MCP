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

### Image-to-Video (Fast)

#### Endpoint Overview

*   **Public Path:** `/generate`
*   **URL:** `https://chutes-wan-2-2-i2v-14b-fast.chutes.ai/generate`
*   **Method:** `POST`
*   **Authentication:** Requests must be authenticated using a Bearer token in the `Authorization` header.

---

#### Input Schema (`I2VArgs`)

##### Required Properties:

*   `prompt` (string): A text description of the desired video.
*   `image` (string): Image URL or base64 encoded data.

##### Optional Properties:

*   `negative_prompt` (string): A text description of what to avoid in the video.
*   `resolution` (string, default: "480p"): The resolution of the video.
*   `fps` (integer, default: 16): The frames per second of the video.
*   `frames` (integer, default: 81): The number of frames to generate.
*   `guidance_scale` (number, default: 1): A parameter to control how much the model should follow the prompt.
*   `guidance_scale_2` (number, default: 1): A second guidance scale parameter.
*   `seed` (integer): A seed for reproducible generation.
*   `fast` (boolean, default: true): Enables ultra fast pruna mode.

---

#### Output (for all endpoints)

*   **Content-Type:** `video/mp4`
*   The response body will be the raw video data.

---

#### Examples

##### `curl` (Image-to-Video - Fast)

```bash
curl -X POST \
    https://chutes-wan-2-2-i2v-14b-fast.chutes.ai/generate \
    -H "Authorization: Bearer $CHUTES_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "fps": 16,
        "fast": true,
        "image": "example-string",
        "prompt": "example-string",
        "resolution": "480p",
        "negative_prompt": "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走",
        "guidance_scale_2": 1
    }'
```

##### Python (`requests`) (Image-to-Video - Fast)

```python
import requests

def invoke_chute():
    api_token = "$CHUTES_API_TOKEN"  # Replace with your actual API token

    headers = {
        "Authorization": "Bearer " + api_token,
        "Content-Type": "application/json"
    }
    
    body = {
      "image": "example-string",
      "frames": 81,
      "prompt": "example-string",
      "negative_prompt": "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走",
      "guidance_scale_2": 1
    }

    response = requests.post(
        "https://chutes-wan-2-2-i2v-14b-fast.chutes.ai/generate",
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