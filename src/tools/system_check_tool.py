import aiohttp
from loguru import logger
from src.mcp_instance import mcp
from src.config import config
from fastmcp.exceptions import ToolError

@mcp.tool(
    name="check_mcp_status",
    description="Checks if the MCP server is running and connected to its configured endpoints (LLM, Image, Music, Video)."
)
async def check_mcp_status() -> str:
    """
    Performs a health check on the MCP server and its external endpoint connections.
    """
    logger.info("Starting MCP system health check.")
    status_messages = []

    # Check MCP server internal status
    if mcp:
        status_messages.append("MCP server instance is initialized and running.")
    else:
        status_messages.append("ERROR: MCP server instance is not initialized.")
        raise ToolError("MCP server instance is not initialized.")

    # Check external endpoint connections
    endpoints_to_check = {
        "LLM": config.get("chutes.endpoints.llm"),
        "Text to Image": config.get("chutes.endpoints.text_to_image"),
        "Text to Music": config.get("chutes.endpoints.text_to_music"),
        "Image to Image": config.get("chutes.endpoints.image_to_image"),
        "Text to Video": config.get("chutes.endpoints.text_to_video"),
        "Image to Video": config.get("chutes.endpoints.image_to_video"),
        "Image to Video Fast": config.get("chutes.endpoints.image_to_video_fast"),
    }

    api_token = config.get("chutes.api_token")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}" if api_token else ""
    }

    async with aiohttp.ClientSession() as session:
        for name, url in endpoints_to_check.items():
            if url:
                try:
                    # Attempt a simple GET request to check connectivity
                    # For some APIs, a HEAD request might be sufficient or more appropriate
                    # but GET is generally supported and we don't need the content.
                    # Timeout added to prevent hanging.
                    async with session.get(url, headers=headers, data="test", timeout=5) as response:
                        if response.status == 400:
                            status_messages.append(f"SUCCESS: {name} endpoint ({url}) is reachable and authorized.")
                        else:
                            status_messages.append(f"WARNING: {name} endpoint ({url}) returned unexpected status {response.status}. Expected 400 for reachability check.")
                except aiohttp.ClientError as e:
                    status_messages.append(f"ERROR: {name} endpoint ({url}) is unreachable. Client Error: {e}")
                except Exception as e:
                    status_messages.append(f"ERROR: {name} endpoint ({url}) encountered an unexpected error: {e}")
            else:
                status_messages.append(f"INFO: {name} endpoint is not configured.")

        # Add Quota Usage check
        if api_token:
            quota_url = "https://api.chutes.ai/users/me/quota_usage/0"
            try:
                async with session.get(quota_url, headers=headers, timeout=5) as response:
                    if response.status == 200:
                        quota_data = await response.json()
                        status_messages.append(f"SUCCESS: Quota Usage API ({quota_url}) is reachable (Status: {response.status}). Quota data: {quota_data}")
                    else:
                        status_messages.append(f"WARNING: Quota Usage API ({quota_url}) returned status {response.status}.")
            except aiohttp.ClientError as e:
                status_messages.append(f"ERROR: Quota Usage API ({quota_url}) is unreachable. Client Error: {e}")
            except Exception as e:
                status_messages.append(f"ERROR: Quota Usage API ({quota_url}) encountered an unexpected error: {e}")
        else:
            status_messages.append("INFO: Chutes API token not configured for Quota Usage check.")


    logger.info("MCP system health check completed.")
    return "\n".join(status_messages)
