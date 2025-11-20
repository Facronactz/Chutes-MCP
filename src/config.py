import os
import yaml
import re
from loguru import logger
import sys
import logging # Import standard logging module

# Remove default Loguru handler that prints to stderr
logger.remove()
# Add a temporary handler to capture logs until proper configuration is loaded
logger.add(sys.stderr, level="INFO")

class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

class Config:
    def __init__(self, config_path='config.yaml'):
        self.config = self._load_config(config_path)
        self._configure_logging()

    def _load_config(self, config_path):
        logger.info(f"Loading configuration from {config_path}...")
        try:
            with open(config_path, 'r') as f:
                config_str = f.read()
            
            # Regex to find all ${VAR_NAME} placeholders
            placeholder_pattern = re.compile(r'\$\{(.*?)\}')
            
            def replace_placeholder(match):
                var_name = match.group(1)
                env_value = os.getenv(var_name, '')
                if env_value:
                    logger.debug(f"Substituting environment variable '{var_name}'.")
                else:
                    logger.debug(f"Environment variable '{var_name}' not found, substituting with empty string.")
                return env_value

            # Substitute all placeholders with environment variables
            resolved_config_str = placeholder_pattern.sub(replace_placeholder, config_str)
            
            config_data = yaml.safe_load(resolved_config_str)
            logger.info("Configuration loaded successfully.")
            return config_data
        except FileNotFoundError:
            logger.error(f"Configuration file not found at {config_path}.")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML in {config_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading config from {config_path}: {e}")
            raise

    def _configure_logging(self):
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        # Get log level from config, default to INFO
        configured_log_level = self.get("logging.level", "INFO").upper()
        
        # Map configured_log_level to a Loguru level
        if configured_log_level == "NONE":
            effective_log_level = logger.level("CRITICAL").no + 1 # Effectively disable logging
            logger.info("Logging level set to NONE (effectively disabled for general output).")
        else:
            try:
                # Validate if the level is a recognized Loguru level
                logger.level(configured_log_level)
                effective_log_level = configured_log_level
                logger.info(f"Logging level set to {effective_log_level}.")
            except ValueError:
                effective_log_level = "INFO"
                logger.warning(f"Invalid logging level '{configured_log_level}' in config.yaml. Defaulting to INFO.")

        logger.remove() # Remove ALL current handlers (including the temporary one)

        # Configure standard logging to use Loguru
        logging.basicConfig(handlers=[InterceptHandler()], level=0)
        logging.getLogger("uvicorn").handlers = [InterceptHandler()]
        logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
        logging.captureWarnings(True)

        # Add file handler for general logs
        logger.add(
            os.path.join(log_dir, 'mcp.log'),
            rotation='500 MB',
            retention='10 days',
            level=effective_log_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            enqueue=True # Asynchronous logging
        )
        # Add file handler for error logs (always ERROR level)
        logger.add(
            "logs/error.log",
            level="ERROR",
            rotation="1 week",
            retention="1 month",
            enqueue=True
        )
        # Add stderr handler for console output
        logger.add(
            os.sys.stderr,
            level=effective_log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        )



    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            logger.debug(f"Retrieved config key '{key}' with value: {value}")
            return value
        except (KeyError, TypeError):
            if default is not None:
                logger.warning(f"Config key '{key}' not found, returning default value: {default}")
            else:
                logger.debug(f"Config key '{key}' not found, returning None.")
            return default

# Global config instance
config = Config()
