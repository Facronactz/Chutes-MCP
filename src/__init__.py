import sys
import os

# Add the project root (the parent directory of 'src') to the Python path.
# This allows absolute imports from 'src' (e.g., `from src.utils.log import log`)
# to work correctly when the application is run from a different context,
# such as the `fastmcp run` command on the hosting platform.
project_root = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
