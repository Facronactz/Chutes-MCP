import os
import yaml
import re
from .utils.log import log, setup_logging, pre_configure_logging

# Perform initial, temporary logging configuration.
pre_configure_logging()

class Config:
    def __init__(self, config_path='config.yaml'):
        self.config = self._load_config(config_path)
        # Set up the logger using the loaded configuration
        setup_logging(self)

    def _load_config(self, config_path):
        log.logger.info(f"Loading configuration from {config_path}...")
        try:
            with open(config_path, 'r') as f:
                config_str = f.read()
            
            # Regex to find all ${VAR_NAME} placeholders
            placeholder_pattern = re.compile(r'\$\{(.*?)\}')
            
            def replace_placeholder(match):
                var_name = match.group(1)
                env_value = os.getenv(var_name, '')
                if env_value:
                    log.logger.debug(f"Substituting environment variable '{var_name}'.")
                else:
                    log.logger.debug(f"Environment variable '{var_name}' not found, substituting with empty string.")
                return env_value

            # Substitute all placeholders with environment variables
            resolved_config_str = placeholder_pattern.sub(replace_placeholder, config_str)
            
            config_data = yaml.safe_load(resolved_config_str)
            log.logger.info("Configuration loaded successfully.")
            return config_data
        except FileNotFoundError:
            log.logger.error(f"Configuration file not found at {config_path}.")
            raise
        except yaml.YAMLError as e:
            log.logger.error(f"Error parsing YAML in {config_path}: {e}")
            raise
        except Exception as e:
            log.logger.error(f"An unexpected error occurred while loading config from {config_path}: {e}")
            raise

    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            log.logger.debug(f"Retrieved config key '{key}' with value: {value}")
            return value
        except (KeyError, TypeError):
            if default is not None:
                log.logger.warning(f"Config key '{key}' not found, returning default value: {default}")
            else:
                log.logger.debug(f"Config key '{key}' not found, returning None.")
            return default

# Global config instance
config = Config()