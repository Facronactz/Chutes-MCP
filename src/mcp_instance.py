from fastmcp import FastMCP
from src.utils.log import log
from src.utils.multimodal_llm import MultimodalLLM

# This file holds the central mcp object to avoid circular dependencies.
log.logger.info("Initializing FastMCP instance...")
mcp = FastMCP("Chutes MCP Server")
mcp.multimodal_llm = MultimodalLLM()
log.logger.info("FastMCP instance initialized.")