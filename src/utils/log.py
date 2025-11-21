import logging
import os
import sys

from loguru import logger

# ======================================================================================
# Part 1: Centralized Logging Configuration
# ======================================================================================

def pre_configure_logging():
    """
    Removes default Loguru handler and adds a temporary one
    to capture logs until proper configuration is loaded.
    """
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

class InterceptHandler(logging.Handler):
    """
    Intercepts standard logging messages and forwards them to Loguru.
    """
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging(config):
    """
    Sets up the application's logging based on the provided configuration object.
    """
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    configured_log_level = config.get("logging.level", "INFO").upper()
    file_logging_enabled = config.get("logging.file_enabled", False)
    
    if configured_log_level == "NONE":
        effective_log_level = logger.level("CRITICAL").no + 1
        logger.info("Logging level set to NONE (effectively disabled for general output).")
    else:
        try:
            logger.level(configured_log_level)
            effective_log_level = configured_log_level
            logger.info(f"Logging level set to {effective_log_level}.")
        except ValueError:
            effective_log_level = "INFO"
            logger.warning(f"Invalid logging level '{configured_log_level}' in config.yaml. Defaulting to INFO.")

    logger.remove()

    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    logging.getLogger("uvicorn").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.captureWarnings(True)

    if file_logging_enabled:
        logger.info("File logging is enabled. Adding file handlers.")
        logger.add(
            os.path.join(log_dir, 'mcp.log'),
            rotation='500 MB',
            retention='10 days',
            level=effective_log_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            enqueue=True
        )
        logger.add(
            "logs/error.log",
            level="ERROR",
            rotation="1 week",
            retention="1 month",
            enqueue=True
        )
    else:
        logger.info("File logging is disabled. Skipping file handlers.")

    logger.add(
        sys.stderr,
        level=effective_log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

# ======================================================================================
# Part 2: Custom Logger Class for Application Use
# ======================================================================================

class CustomLogger:
    """
    A logging utility that logs to the globally configured Loguru logger
    and also to the FastMCP context when available.
    """

    def __init__(self):
        self._local_logger = logger
        self._get_context_func = None
        try:
            from fastmcp.server.dependencies import get_context
            self._get_context_func = get_context
        except ImportError:
            pass

    def _get_context(self):
        if not self._get_context_func:
            return None
        try:
            return self._get_context_func()
        except RuntimeError:
            return None

    async def debug(self, message: str, *args, **kwargs):
        """Logs a debug message to the local logger and to the context (if available)."""
        self._local_logger.debug(message, *args, **kwargs)
        context = self._get_context()
        if context:
            await context.debug(message, *args, **kwargs)

    async def info(self, message: str, *args, **kwargs):
        """Logs an info message to the local logger and to the context (if available)."""
        self._local_logger.info(message, *args, **kwargs)
        context = self._get_context()
        if context:
            await context.info(message, *args, **kwargs)

    async def warning(self, message: str, *args, **kwargs):
        """Logs a warning message to the local logger and to the context (if available)."""
        self._local_logger.warning(message, *args, **kwargs)
        context = self._get_context()
        if context:
            await context.warning(message, *args, **kwargs)

    async def error(self, message: str, *args, **kwargs):
        """Logs an error message to the local logger and to the context (if available)."""
        self._local_logger.error(message, *args, **kwargs)
        context = self._get_context()
        if context:
            await context.error(message, *args, **kwargs)

    @property
    def logger(self):
        """Returns the underlying loguru logger instance for non-async use."""
        return self._local_logger

# ======================================================================================
# Part 3: Export a Singleton Instance
# ======================================================================================

log = CustomLogger()
