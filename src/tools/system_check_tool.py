import aiohttp
from loguru import logger
from src.mcp_instance import mcp
from src.config import config
from fastmcp.exceptions import ToolError
from typing import Annotated, List, Dict, Union # Added Annotated, List, Dict, Union
from pydantic import Field # Added Field
from fastmcp.tools.tool import ToolResult # Added ToolResult
from mcp.types import TextContent # Added TextContent

@mcp.tool(
    name="check_mcp_status",
    description="Checks if the MCP server is running and connected to its configured endpoints (LLM, Image, Music, Video).",
    annotations={
        "title": "Check MCP Status",
        "readOnlyHint": True,  # It only checks status, doesn't modify anything
        "openWorldHint": True   # It interacts with external APIs
    }
)
async def check_mcp_status() -> ToolResult: # Changed return type to ToolResult
    """
    Performs a health check on the MCP server and its external endpoint connections.
    """
    logger.info("Starting MCP system health check.")
    status_messages = []
    structured_statuses = [] # New list for structured data

    # Check MCP server internal status
    mcp_status = {"component": "MCP Server Instance", "status": "UNKNOWN", "details": ""}
    if mcp:
        mcp_status["status"] = "SUCCESS"
        mcp_status["details"] = "MCP server instance is initialized and running."
        status_messages.append(mcp_status["details"])
    else:
        mcp_status["status"] = "ERROR"
        mcp_status["details"] = "MCP server instance is not initialized."
        status_messages.append(mcp_status["details"])
        # Do not raise ToolError here, collect all statuses before returning.
    structured_statuses.append(mcp_status)

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
            check_result = {"component": name, "status": "UNKNOWN", "details": ""}
            if url:
                try:
                    async with session.get(url, headers=headers, data="test", timeout=5) as response:
                        if response.status == 400: # Assuming 400 is expected for a basic reachability check without proper payload
                            check_result["status"] = "SUCCESS"
                            check_result["details"] = f"Endpoint is reachable and authorized (expected 400 status)."
                            status_messages.append(f"SUCCESS: {name} endpoint ({url}) is reachable and authorized.")
                        else:
                            check_result["status"] = "WARNING"
                            check_result["details"] = f"Returned unexpected status {response.status}. Expected 400 for reachability check."
                            status_messages.append(f"WARNING: {name} endpoint ({url}) returned unexpected status {response.status}. Expected 400 for reachability check.")
                except aiohttp.ClientError as e:
                    check_result["status"] = "ERROR"
                    check_result["details"] = f"Endpoint is unreachable. Client Error: {e}"
                    status_messages.append(f"ERROR: {name} endpoint ({url}) is unreachable. Client Error: {e}")
                except Exception as e:
                    check_result["status"] = "ERROR"
                    check_result["details"] = f"Encountered an unexpected error: {e}"
                    status_messages.append(f"ERROR: {name} endpoint ({url}) encountered an unexpected error: {e}")
            else:
                check_result["status"] = "INFO"
                check_result["details"] = "Endpoint is not configured."
                status_messages.append(f"INFO: {name} endpoint is not configured.")
            structured_statuses.append(check_result)

        # Add Quota Usage check
        quota_check_result = {"component": "Quota Usage API", "status": "UNKNOWN", "details": ""}
        if api_token:
            quota_url = "https://api.chutes.ai/users/me/quota_usage/0"
            try:
                async with session.get(quota_url, headers=headers, timeout=5) as response:
                    if response.status == 200:
                        quota_data = await response.json()
                        quota_check_result["status"] = "SUCCESS"
                        quota_check_result["details"] = f"API is reachable (Status: {response.status}). Quota data: {quota_data}"
                        status_messages.append(f"SUCCESS: Quota Usage API ({quota_url}) is reachable (Status: {response.status}). Quota data: {quota_data}")
                    else:
                        quota_check_result["status"] = "WARNING"
                        quota_check_result["details"] = f"Returned status {response.status}."
                        status_messages.append(f"WARNING: Quota Usage API ({quota_url}) returned status {response.status}.")
            except aiohttp.ClientError as e:
                quota_check_result["status"] = "ERROR"
                quota_check_result["details"] = f"API is unreachable. Client Error: {e}"
                status_messages.append(f"ERROR: Quota Usage API ({quota_url}) is unreachable. Client Error: {e}")
            except Exception as e:
                quota_check_result["status"] = "ERROR"
                quota_check_result["details"] = f"Encountered an unexpected error: {e}"
                status_messages.append(f"ERROR: Quota Usage API ({quota_url}) encountered an unexpected error: {e}")
        else:
            quota_check_result["status"] = "INFO"
            quota_check_result["details"] = "Chutes API token not configured for Quota Usage check."
            status_messages.append("INFO: Chutes API token not configured for Quota Usage check.")
        structured_statuses.append(quota_check_result)


    logger.info("MCP system health check completed.")
    
    return ToolResult(
        content=[TextContent(type="text", text="\n".join(status_messages))],
        structured_content={"checks": structured_statuses}
    )
