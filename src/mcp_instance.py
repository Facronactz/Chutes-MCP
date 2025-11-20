from fastmcp import FastMCP
from loguru import logger
from src.utils.multimodal_llm import MultimodalLLM

# This file holds the central mcp object to avoid circular dependencies.
logger.info("Initializing FastMCP instance...")
mcp = FastMCP("Chutes MCP Server")
mcp.multimodal_llm = MultimodalLLM()
logger.info("FastMCP instance initialized.")