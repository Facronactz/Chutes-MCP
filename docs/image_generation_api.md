### Chutes Image Generation API Documentation

This document outlines the schema for the Chutes image generation endpoint.

#### Endpoint Overview

*   **Public Path:** `/generate`
*   **URL:** `https://image.chutes.ai/generate`
*   **Method:** `POST`
*   **Authentication:** Requests must be authenticated using a Bearer token in the `Authorization` header.
    *   Example: `Authorization: Bearer YOUR_CHUTES_API_TOKEN`

---

#### Input Schema (`GenerationInput`)

The body of your `POST` request should be a JSON object that conforms to the `GenerationInput` schema.

##### Required Properties:

*   `prompt` (string): A text description of the desired image.

##### Optional Properties:

*   `negative_prompt` (string): A text description of what to avoid in the image.
*   `width` (integer, default: 1024): The width of the generated image.
*   `height` (integer, default: 1024): The height of the generated image.
*   `num_inference_steps` (integer, default: 50): The number of denoising steps.
*   `seed` (integer): A seed for reproducible generation.
*   `true_cfg_scale` (number, default: 4): A parameter to control how much the model should follow the prompt.

---

#### Output

*   **Content-Type:** `image/jpeg`
*   The response body will be the raw image data.

---

#### Examples

Here are some examples of how to call the endpoint.

##### `curl`

```bash
curl -X POST \
    https://image.chutes.ai/generate \
    -H "Authorization: Bearer $CHUTES_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "qwen-image",
        "prompt": "A beautiful sunset over mountains",
        "negative_prompt": "blur, distortion, low quality",
        "guidance_scale": 7.5,
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 50
    }'
```

##### Python (`aiohttp`)

```python
import aiohttp
import asyncio

async def invoke_chute():
    api_token = "$CHUTES_API_TOKEN"  # Replace with your actual API token

    headers = {
        "Authorization": "Bearer " + api_token,
        "Content-Type": "application/json"
    }
    
    body = {
      "model": "qwen-image",
      "prompt": "A beautiful sunset over mountains",
      "negative_prompt": "blur, distortion, low quality",
      "guidance_scale": 7.5,
      "width": 1024,
      "height": 1024,
      "num_inference_steps": 50
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://image.chutes.ai/generate", 
            headers=headers,
            json=body
        ) as response:
            # The response content will be the image bytes
            # You can save it to a file like this:
            with open("generated_image.jpg", "wb") as f:
                f.write(await response.read())

asyncio.run(invoke_chute())
```
