import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    # Import the app object from src.app
    from src.app import mcp
    # Import the main module to ensure tools are loaded
    import src.main
    
    # Get host and port from environment variables with defaults
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))

    # Run the MCP server
    mcp.run(transport="http", host=host, port=port)
