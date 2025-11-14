# This file is used to ensure that all tools are loaded.
# By importing the modules containing the tools, we make sure the @mcp.tool decorator is executed.

from .tools import llm_tool
from .tools import image_tool
from .tools import music_tool
