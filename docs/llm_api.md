### Chutes LLM Endpoint Documentation

This document outlines the schema for the Chutes LLM chat completions endpoint, which allows for generating text from a large language model.

#### Endpoint Overview

*   **Public Path:** `/v1/chat/completions`
*   **Method:** `POST`
*   **Streaming:** The endpoint supports streaming responses, which is ideal for real-time applications.
*   **Authentication:** Requests must be authenticated using a Bearer token in the `Authorization` header.
    *   Example: `Authorization: Bearer YOUR_CHUTES_API_TOKEN`

---

#### Input Schema (`ChatCompletionRequest`)

The main body of your `POST` request should be a JSON object that conforms to the `ChatCompletionRequest` schema.

##### Required Properties:

*   `model` (string): The ID of the model to use for the completion.
    *   Example: `"deepseek-ai/DeepSeek-R1-0528"`
*   `messages` (array of `ChatMessage` objects): A list of messages describing the conversation history.
    *   A `ChatMessage` object has two properties:
        *   `role` (string): The role of the message author (e.g., `"user"`, `"assistant"`).
        *   `content` (string): The content of the message.

##### Optional Properties (Common):

*   `stream` (boolean, default: `false`): If set to `true`, the response will be sent as a stream of events.
*   `temperature` (number, default: `0.7`): Controls the randomness of the output. Higher values make the output more random, while lower values make it more deterministic.
*   `max_tokens` (integer, default: `null`): The maximum number of tokens to generate in the completion.
*   `top_p` (number, default: `1`): An alternative to `temperature` that uses nucleus sampling.
*   `stop` (string or array of strings): Sequences where the API will stop generating further tokens.
*   `response_format` (object): Specifies the format of the output. Can be used to enforce JSON output.

---

#### Output Schema (Streaming)

When `stream` is set to `true`, the server will send a stream of JSON objects, each separated by a newline.

Each JSON object in the stream represents a chunk of the completion and contains the following key properties:

*   `choices` (array of `ChatCompletionResponseStreamChoice` objects): A list of completion choices. For streaming, this will typically contain one choice.
    *   `delta` (object): Contains the incremental update to the message.
        *   `content` (string): The new token(s) of text.
        *   `role` (string): The role of the assistant, usually present only in the first chunk.
    *   `finish_reason` (string): The reason the model stopped generating tokens. This will be `null` until the final chunk, where it might be `"stop"` or `"length"`.
*   `usage` (`UsageInfo` object): Present in the last chunk of the stream, this object provides information about the number of tokens used.

---

#### Minimal Input Schema

The endpoint also defines a `minimal_input_schema`, which provides more default values for a simpler request structure. This is useful for quick tests or when you don't need to customize many parameters.

---

#### Examples

Here are some examples of how to call the endpoint.

##### `curl`

```bash
curl -X POST \
    https://llm.chutes.ai/v1/chat/completions \
    -H "Authorization: Bearer $CHUTES_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "deepseek-ai/DeepSeek-R1-0528",
        "messages": [
            {
                "role": "user",
                "content": "Tell me a 250 word story."
            }
        ],
        "stream": true,
        "max_tokens": 1024,
        "temperature": 0.7
    }'
```

##### Python (`aiohttp`)

```python
import aiohttp
import asyncio
import json

async def invoke_chute():
    api_token = "$CHUTES_API_TOKEN"  # Replace with your actual API token

    headers = {
        "Authorization": "Bearer " + api_token,
        "Content-Type": "application/json"
    }
    
    body = {
      "model": "deepseek-ai/DeepSeek-R1-0528",
      "messages": [
        {
          "role": "user",
          "content": "Tell me a 250 word story."
        }
      ],
      "stream": True,
      "max_tokens": 1024,
      "temperature": 0.7
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://llm.chutes.ai/v1/chat/completions", 
            headers=headers,
            json=body
        ) as response:
            async for line in response.content:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = data.strip()
                        if chunk:
                            print(chunk)
                    except Exception as e:
                        print(f"Error parsing chunk: {e}")

asyncio.run(invoke_chute())
```
