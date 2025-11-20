from fastmcp import FastMCP
from loguru import logger

# This file holds the central mcp object to avoid circular dependencies.
logger.info("Initializing FastMCP instance...")
mcp = FastMCP("Chutes MCP Server")
logger.info("FastMCP instance initialized.")