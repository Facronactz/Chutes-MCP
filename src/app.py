import sys
import os
from dotenv import load_dotenv
from loguru import logger

logger.info("Starting application setup in app.py...")

# Add the project root to the Python path to allow absolute imports from 'src'.
# This is necessary because fastmcp dev runs this file as a top-level script
# without adding the project root to the path automatically.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.debug(f"Added project root to sys.path: {project_root}")

# Import the central mcp object
from src.mcp_instance import mcp

logger.info("Loading environment variables...")
load_dotenv()
logger.info("Environment variables loaded.")

# Import main to load the tools, which will decorate the mcp object
logger.info("Importing tool modules...")
from src.tools import llm_tool
logger.debug("LLM tool module imported.")
from src.tools import image_tool
logger.debug("Image tool module imported.")
from src.tools import music_tool
logger.debug("Music tool module imported.")
from src.tools import video_tool
logger.debug("Video tool module imported.")
from src.tools import system_check_tool
logger.debug("System Check tool module imported.")
logger.info("All tool modules imported.")

# The mcp object is now decorated with tools and ready to be used.
# start.py will import this mcp object.
