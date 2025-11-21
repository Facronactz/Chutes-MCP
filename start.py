import os
from dotenv import load_dotenv
# Import the pre-configuration from the new logging utility
from src.utils.log import pre_configure_logging, log

# It's important to run pre-configuration before any other imports that might log
pre_configure_logging()

log.logger.info("Starting MCP Server application...")

# Load environment variables from .env file
log.logger.info("Loading environment variables...")
load_dotenv()
log.logger.info("Environment variables loaded.")

if __name__ == "__main__":
    try:
        # Import the app object from src.app
        log.logger.info("Importing MCP application instance...")
        from src.app import mcp
        log.logger.info("MCP application instance imported successfully.")
        
        # Get host and port from environment variables with defaults
        host = os.getenv("MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_PORT", "8000"))
        log.logger.info(f"Configuring MCP server to run on host: {host}, port: {port}")

        # Run the MCP server
        log.logger.info("Starting MCP server...")
        mcp.run(transport="http", host=host, port=port)
        log.logger.info("MCP server started successfully.")
    except Exception as e:
        log.logger.critical(f"An unhandled exception occurred during MCP server startup: {e}", exc_info=True)
        # Optionally re-raise or exit, depending on desired behavior
        # raise
