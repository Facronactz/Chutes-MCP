### Chutes Image Editing API Documentation

This document outlines the schema for the Chutes image editing endpoint.

#### Endpoint Overview

*   **Public Path:** `/generate`
*   **URL:** `https://chutes-qwen-image-edit-2509.chutes.ai/generate`
*   **Method:** `POST`
*   **Authentication:** Requests must be authenticated using a Bearer token in the `Authorization` header.
    *   Example: `Authorization: Bearer YOUR_CHUTES_API_TOKEN`

---

#### Input Schema (`GenerationInput`)

The body of your `POST` request should be a JSON object that conforms to the `GenerationInput` schema.

##### Required Properties:

*   `prompt` (string): A text description of the desired edit.
*   `image_b64s` (array of strings): A list of base64 encoded images to be edited.

##### Optional Properties:

*   `negative_prompt` (string): A text description of what to avoid in the image.
*   `width` (integer, default: 1024): The width of the generated image.
*   `height` (integer, default: 1024): The height of the generated image.
*   `num_inference_steps` (integer, default: 40): The number of denoising steps.
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
    https://chutes-qwen-image-edit-2509.chutes.ai/generate \
    -H "Authorization: Bearer $CHUTES_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d 
    {
        "seed": null,
        "width": 1024,
        "height": 1024,
        "prompt": "example-string",
        "image_b64s": [
            "example-string"
        ],
        "true_cfg_scale": 4,
        "negative_prompt": "",
        "num_inference_steps": 40
    }
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
      "seed": null,
      "width": 1024,
      "height": 1024,
      "prompt": "example-string",
      "image_b64s": [
        "example-string"
      ],
      "true_cfg_scale": 4,
      "negative_prompt": "",
      "num_inference_steps": 40
    }

    response = requests.post(
        "https://chutes-qwen-image-edit-2509.chutes.ai/generate",
        headers=headers,
        json=body
    )

    # The response content will be the image bytes
    # You can save it to a file like this:
    if response.status_code == 200:
        with open("edited_image.jpg", "wb") as f:
            f.write(response.content)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

invoke_chute()
```
