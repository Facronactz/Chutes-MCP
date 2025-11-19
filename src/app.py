import sys
import os
from dotenv import load_dotenv

# Add the project root to the Python path to allow absolute imports from 'src'.
# This is necessary because fastmcp dev runs this file as a top-level script
# without adding the project root to the path automatically.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the central mcp object
from src.mcp_instance import mcp

load_dotenv()

# Import main to load the tools, which will decorate the mcp object
from src.tools import llm_tool
from src.tools import image_tool
from src.tools import music_tool
from src.tools import video_tool


# The mcp object is now decorated with tools and ready to be used.
# start.py will import this mcp object.
