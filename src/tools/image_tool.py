import os
import aiohttp
from loguru import logger
import requests
import uuid
from typing import Optional, List, Union, Dict, Annotated
from fastmcp import Context
from fastmcp.exceptions import ToolError
from src.mcp_instance import mcp
from src.config import config
from fastmcp.utilities.types import Image
from src.utils.imagekit_uploader import upload_to_imagekit
from pydantic import Field
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent


@mcp.tool(
    name="generate_image",
    description="Generates an image from a text prompt. By default, uploads the image to ImageKit as a side effect. If `analyze_image_with_llm` is True, returns a dictionary containing the generated Image object and the LLM's analysis of the image.",
    annotations={
        "title": "Generate Image",
        "readOnlyHint": False,  # Because it uploads to ImageKit
        "openWorldHint": True   # Because it calls external APIs
    }
)
async def generate_image(
    context: Context,
    prompt: Annotated[str, Field(description="A detailed text description of the image to be generated. Be specific about subjects, styles, and mood.")],
    negative_prompt: Annotated[Optional[str], Field(description="A text description of elements or styles to avoid in the generated image.")] = None,
    width: Annotated[int, Field(description="The width of the generated image in pixels.", ge=256, le=2048)] = 1024,
    height: Annotated[int, Field(description="The height of the generated image in pixels.", ge=256, le=2048)] = 1024,
    num_inference_steps: Annotated[int, Field(description="The number of denoising steps for image generation. Higher values can improve quality but increase generation time.", ge=10, le=60)] = 25,
    seed: Annotated[Optional[int], Field(description="An optional seed for reproducible image generation. If not provided, a random seed will be used.")] = None,
    save_to_file: Annotated[bool, Field(description="If True, the generated image will be uploaded to ImageKit for persistent storage and URL access.")] = True,
    analyze_image_with_llm: Annotated[bool, Field(description="If True, the generated image will be sent to an LLM for detailed analysis and description.")] = False,
) -> Union[Image, ToolResult]:
    """
    Generates an image using the Chutes image generation API.

    :param prompt: A text description of the desired image.
    :param negative_prompt: A text description of what to avoid in the image.
    :param width: The width of the generated image.
    :param height: The height of the generated image.
    :param num_inference_steps: The number of denoising steps.
    :param seed: A seed for reproducible generation.
    :param save_to_file: If True, uploads the image to ImageKit as a side effect.
    :param analyze_image_with_llm: If True, the generated image will be analyzed by an LLM.
    :return: An Image object on success, or an error message string. If analyze_image_with_llm is True,
             returns a dictionary containing the Image object and the LLM's analysis.
    """
    await context.info("Entering generate_image function.")
    await context.debug(f"Generate Image Parameters: prompt='{prompt}', negative_prompt='{negative_prompt}', width={width}, height={height}, num_inference_steps={num_inference_steps}, seed={seed}, save_to_file={save_to_file}, analyze_image_with_llm={analyze_image_with_llm}")

    base_steps = 3  # Prepare, Call API, Receive Data
    total_steps = base_steps + (1 if save_to_file else 0) + (1 if analyze_image_with_llm else 0)
    current_progress = 0

    await context.report_progress(progress=current_progress, total=total_steps, message="Initializing image generation request.")
    current_progress += 1

    if num_inference_steps > 60:
        await context.error(f"num_inference_steps (got {num_inference_steps}) cannot exceed 60.")
        raise ToolError("num_inference_steps cannot exceed 60.")

    api_token = config.get("chutes.api_token")
    if not api_token:
        await context.warning("CHUTES_API_TOKEN environment variable not set for generate_image.")
        raise ToolError("CHUTES_API_TOKEN environment variable not set.")

    image_endpoint = config.get("chutes.endpoints.text_to_image")
    if not image_endpoint:
        await context.warning("Text-to-image endpoint not configured in config.yaml for generate_image.")
        raise ToolError("Text-to-image endpoint not configured in config.yaml.")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    if negative_prompt is None:
        negative_prompt = ""

    body = {
        "model": config.get("chutes.models.text_to_image"),
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "num_inference_steps": num_inference_steps,
        "seed": seed,
    }

    try:
        await context.report_progress(progress=current_progress, total=total_steps, message="Calling Chutes Image API for generation.")
        await context.info(f"Calling Chutes Image API at {image_endpoint} for image generation.")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                image_endpoint,
                headers=headers,
                json=body
            ) as response:
                response.raise_for_status()
                image_data = await response.read()
        await context.info("Successfully received image data from Chutes Image API.")
        current_progress += 1
        await context.report_progress(progress=current_progress, total=total_steps, message="Image data received.")

        url = None
        if save_to_file:
            current_progress += 1
            await context.report_progress(progress=current_progress, total=total_steps, message="Uploading generated image to ImageKit.")
            await context.debug("Uploading generated image to ImageKit.")
            metadata = {
                "model": config.get("metadata.models.text_to_image"),
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_inference_steps": num_inference_steps,
                "seed": seed,
            }
            url = upload_to_imagekit(image_data, "generated_image", metadata, "jpeg")
            if url:
                await context.info(f"Generated image uploaded to ImageKit: {url}")
            else:
                await context.error("Failed to upload generated image to ImageKit.")
        
        generated_image_obj = Image(data=image_data, format="jpeg", annotations={"imagekit_url": url} if url else None)
        
        if analyze_image_with_llm:
            current_progress += 1
            await context.report_progress(progress=current_progress, total=total_steps, message="Analyzing generated image with LLM.")
            await context.info("Analyzing generated image with LLM.")
            analysis_prompt = "Describe this image in detail and identify any key objects or themes."
            llm_analysis = await mcp.multimodal_llm.ask_with_images(
                prompt=analysis_prompt,
                images=[image_data]
            )
            await context.info("LLM image analysis complete.")
            
            # Prepare content for ToolResult
            human_readable_content = [
                TextContent(type="text", text=f"Generated image and its analysis:\n{llm_analysis}"),
                generated_image_obj # The Image object will be automatically converted to ImageContent
            ]
            
            structured_data = {
                "image_url": url,
                "llm_analysis": llm_analysis,
                "image_details": {
                    "width": width,
                    "height": height,
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "num_inference_steps": num_inference_steps,
                    "seed": seed,
                }
            }
            
            await context.report_progress(progress=total_steps, total=total_steps, message="Image analysis complete. Returning result.")
            return ToolResult(
                content=human_readable_content,
                structured_content=structured_data
            )
        
        await context.report_progress(progress=total_steps, total=total_steps, message="Image generation complete. Returning result.")
        await context.info("Exiting generate_image function with successful response.")
        return generated_image_obj

    except aiohttp.ClientError as e:
        await context.error(f"AIOHTTP ClientError calling Chutes Image API in generate_image: {e}")
        raise ToolError(f"Error calling Chutes Image API: {e}")
    except Exception as e:
        await context.error(f"An unexpected error occurred in generate_image: {e}", exc_info=True)
        raise ToolError(f"An unexpected error occurred: {e}")

@mcp.tool(
    name="edit_image",
    description="Edits an image based on a text prompt. By default, uploads the image to ImageKit as a side effect.",
    annotations={
        "title": "Edit Image",
        "readOnlyHint": False,  # Because it uploads to ImageKit
        "openWorldHint": True   # Because it calls external APIs
    }
)
async def edit_image( # Changed to async def
    context: Context,
    prompt: Annotated[str, Field(description="A text description of the desired edit.")],
    image_b64s: Annotated[List[str], Field(description="A list of base64 encoded images to be edited.")],
    negative_prompt: Annotated[Optional[str], Field(description="A text description of what to avoid in the image.")] = "",
    width: Annotated[int, Field(description="The width of the generated image.", ge=256, le=2048)] = 1024,
    height: Annotated[int, Field(description="The height of the generated image.", ge=256, le=2048)] = 1024,
    num_inference_steps: Annotated[int, Field(description="The number of denoising steps.", ge=10, le=60)] = 30,
    seed: Annotated[Optional[int], Field(description="A seed for reproducible generation.")] = None,
    true_cfg_scale: Annotated[float, Field(description="A parameter to control how much the model should follow the prompt.", ge=1.0, le=20.0)] = 4.0,
    save_to_file: Annotated[bool, Field(description="If True, uploads the image to ImageKit as a side effect.")] = True,
) -> Union[Image, str]:
    """
    Edits an image using the Chutes image editing API.

    :param prompt: A text description of the desired edit.
    :param image_b64s: A list of base64 encoded images to be edited.
    :param negative_prompt: A text description of what to avoid in the image.
    :param width: The width of the generated image.
    :param height: The height of the generated image.
    :param num_inference_steps: The number of denoising steps.
    :param seed: A seed for reproducible generation.
    :param true_cfg_scale: A parameter to control how much the model should follow the prompt.
    :param save_to_file: If True, uploads the image to ImageKit as a side effect.
    :return: An Image object on success, or an error message string.
    """
    await context.info("Entering edit_image function.")
    await context.debug(f"Edit Image Parameters: prompt='{prompt}', width={width}, height={height}, num_inference_steps={num_inference_steps}, seed={seed}, true_cfg_scale={true_cfg_scale}, save_to_file={save_to_file}")

    base_steps = 3  # Prepare, Call API, Receive Data
    total_steps = base_steps + (1 if save_to_file else 0)
    current_progress = 0

    await context.report_progress(progress=current_progress, total=total_steps, message="Initializing image editing request.")
    current_progress += 1

    api_token = config.get("chutes.api_token")
    if not api_token:
        await context.warning("CHUTES_API_TOKEN environment variable not set for edit_image.")
        raise ToolError("CHUTES_API_TOKEN environment variable not set.")

    image_edit_endpoint = config.get("chutes.endpoints.image_to_image")
    if not image_edit_endpoint:
        await context.warning("Image-to-image endpoint not configured in config.yaml for edit_image.")
        raise ToolError("Image-to-image endpoint not configured in config.yaml.")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    body = {
        "prompt": prompt,
        "image_b64s": image_b64s,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "num_inference_steps": num_inference_steps,
        "seed": seed,
        "true_cfg_scale": true_cfg_scale,
    }

    try:
        await context.report_progress(progress=current_progress, total=total_steps, message="Calling Chutes Image Edit API for editing.")
        await context.info(f"Calling Chutes Image Edit API at {image_edit_endpoint} for image editing.")
        async with aiohttp.ClientSession() as session: # Changed to aiohttp
            async with session.post( # Changed to aiohttp
                image_edit_endpoint,
                headers=headers,
                json=body
            ) as response:
                response.raise_for_status()
                image_data = await response.read() # Changed to await response.read()
        await context.info("Successfully received edited image data from Chutes Image Edit API.")
        current_progress += 1
        await context.report_progress(progress=current_progress, total=total_steps, message="Edited image data received.")

        url = None
        if save_to_file:
            current_progress += 1
            await context.report_progress(progress=current_progress, total=total_steps, message="Uploading edited image to ImageKit.")
            await context.debug("Uploading edited image to ImageKit.")
            metadata = {
                "model": config.get("metadata.models.image_to_image"),
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_inference_steps": num_inference_steps,
                "seed": seed,
                "true_cfg_scale": true_cfg_scale,
            }
            url = upload_to_imagekit(image_data, "edited_image", metadata, "jpeg")
            if url:
                await context.info(f"Edited image uploaded to ImageKit: {url}")
            else:
                await context.error("Failed to upload edited image to ImageKit.")
        
        await context.report_progress(progress=total_steps, total=total_steps, message="Image editing complete. Returning result.")
        await context.info("Exiting edit_image function with successful response.")
        return Image(data=image_data, format="jpeg", annotations={"imagekit_url": url} if url else None)

    except aiohttp.ClientError as e: # Changed exception type
        await context.error(f"AIOHTTP ClientError calling Chutes Image Edit API in edit_image: {e}")
        raise ToolError(f"Error calling Chutes Image Edit API: {e}")
    except Exception as e:
        await context.error(f"An unexpected error occurred in edit_image: {e}", exc_info=True)
        raise ToolError(f"An unexpected error occurred: {e}")

@mcp.tool(
    name="describe_image",
    description="Analyzes an image and provides a detailed description using a multimodal LLM.",
    annotations={
        "title": "Describe Image",
        "readOnlyHint": True,   # It only describes, doesn't modify
        "openWorldHint": True    # It interacts with an external LLM
    }
)
async def describe_image(
    context: Context,
    image_b64s: Annotated[List[str], Field(description="A list of base64 encoded images to be described.")],
    prompt: Annotated[str, Field(description="The prompt to send to the LLM for image description.")] = "Describe this image in detail and identify any key objects or themes.",
) -> str:
    """
    Describes an image using the Chutes Multimodal LLM.

    :param image_b64s: A list of base64 encoded images to be described.
    :param prompt: The prompt to send to the LLM for image description.
    :return: A string containing the LLM's description of the image.
    """
    await context.info("Entering describe_image function.")
    await context.debug(f"Describe Image Parameters: prompt='{prompt}', number of images={len(image_b64s)}")

    total_steps = 3 # Prepare, Call LLM, Receive Data
    current_progress = 0

    await context.report_progress(progress=current_progress, total=total_steps, message="Initializing image description request.")
    current_progress += 1

    if not image_b64s:
        raise ToolError("No images provided for description.")

    try:
        await context.report_progress(progress=current_progress, total=total_steps, message="Calling Multimodal LLM for image description.")
        await context.info("Calling Multimodal LLM for image description.")
        llm_description = await mcp.multimodal_llm.ask_with_images(
            prompt=prompt,
            images=image_b64s
        )
        await context.info("Multimodal LLM image description complete.")
        current_progress += 1
        await context.report_progress(progress=current_progress, total=total_steps, message="Image description received. Returning result.")
        return llm_description
    except Exception as e:
        await context.error(f"An unexpected error occurred in describe_image: {e}", exc_info=True)
        raise ToolError(f"An unexpected error occurred: {e}")
