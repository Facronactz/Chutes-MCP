import os
import yaml
import re

class Config:
    def __init__(self, config_path='config.yaml'):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path):
        with open(config_path, 'r') as f:
            config_str = f.read()
        
        # Regex to find all ${VAR_NAME} placeholders
        placeholder_pattern = re.compile(r'\$\{(.*?)\}')
        
        def replace_placeholder(match):
            var_name = match.group(1)
            return os.getenv(var_name, '')

        # Substitute all placeholders with environment variables
        resolved_config_str = placeholder_pattern.sub(replace_placeholder, config_str)
        
        return yaml.safe_load(resolved_config_str)

    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

# Global config instance
config = Config()
