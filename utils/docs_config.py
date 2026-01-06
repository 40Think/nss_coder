#!/usr/bin/env python3
"""
DocsConfig - Configuration Loader for Documentation System

<!--TAG:docs_utils_config-->

PURPOSE:
    Loads configuration from docs/config/docs_config.yaml.
    Independent from main project's utils/config_loader.py.
    Supports environment variable overrides.

<!--/TAG:docs_utils_config-->
"""

import os
from pathlib import Path
from typing import Any, Optional

# Try to import yaml, graceful fallback
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Docs directory
DOCS_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = DOCS_DIR / "config" / "docs_config.yaml"


class DocsConfig:
    """
    Configuration manager for documentation system.
    
    Loads from docs/config/docs_config.yaml with env var overrides.
    """
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(DocsConfig, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from YAML file."""
        self._config = {}
        
        if not YAML_AVAILABLE:
            return
        
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception:
                pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Priority:
        1. Environment variable (DOCS_{KEY})
        2. Config file value
        3. Default value
        
        Supports nested keys with dot notation: 'llm.endpoint'
        """
        # Check environment variable first
        env_key = f"DOCS_{key.upper().replace('.', '_')}"
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value
        
        # Navigate nested config
        value = self._config
        for part in key.split('.'):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
                break
        
        return value if value is not None else default
    
    def get_path(self, key: str, default: str = None) -> Optional[Path]:
        """Get configuration value as Path, relative to docs/."""
        value = self.get(key, default)
        if value is None:
            return None
        return DOCS_DIR / value
    
    def reload(self):
        """Reload configuration from file."""
        self._load_config()


# Singleton instance
docs_config = DocsConfig()


def get_config(key: str, default: Any = None) -> Any:
    """Convenience function to get config value."""
    return docs_config.get(key, default)
