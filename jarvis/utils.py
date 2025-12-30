"""
Utilities Module - Helper functions for JARVIS
Config loading, validation, and common utilities
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_project_root() -> Path:
    """
    Get the root directory of the JARVIS project
    
    Returns:
        Path object for project root
    """
    # Assumes jarvis/ is in project root
    return Path(__file__).parent.parent


def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from config/config.json
    
    Args:
        config_file: Optional path to config file. Uses default if not provided.
    
    Returns:
        Configuration dictionary
    
    Raises:
        FileNotFoundError: If config file not found
        json.JSONDecodeError: If config JSON is invalid
    """
    if config_file is None:
        config_file = get_project_root() / "config" / "config.json"
    else:
        config_file = Path(config_file)

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with open(config_file, 'r') as f:
        config = json.load(f)

    return config


def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get environment variable with optional default
    
    Args:
        key: Environment variable name
        default: Default value if not set
    
    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)


def validate_api_key(provider: str) -> bool:
    """
    Check if API key is set for a provider
    
    Args:
        provider: Provider name (openai, deepseek, gemini, custom)
    
    Returns:
        True if API key is set, False otherwise
    """
    env_keys = {
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "custom": "CUSTOM_AI_API_KEY",
    }

    env_key = env_keys.get(provider.lower())
    if not env_key:
        return False

    return bool(os.getenv(env_key))


def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key for a provider
    
    Args:
        provider: Provider name
    
    Returns:
        API key or None if not set
    """
    env_keys = {
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "custom": "CUSTOM_AI_API_KEY",
    }

    env_key = env_keys.get(provider.lower())
    if not env_key:
        return None

    return os.getenv(env_key)


def merge_dicts(base: Dict, override: Dict) -> Dict:
    """
    Deep merge override dict into base dict
    
    Args:
        base: Base dictionary
        override: Dictionary with overrides
    
    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def ensure_dir(path: Path) -> Path:
    """
    Ensure directory exists
    
    Args:
        path: Directory path
    
    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_read_file(file_path: str) -> Optional[str]:
    """
    Safely read a file with error handling
    
    Args:
        file_path: Path to file
    
    Returns:
        File contents or None if error
    """
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


def safe_write_file(file_path: str, content: str, append: bool = False) -> bool:
    """
    Safely write to a file with error handling
    
    Args:
        file_path: Path to file
        content: Content to write
        append: Append to file instead of overwriting
    
    Returns:
        True if successful, False otherwise
    """
    try:
        mode = 'a' if append else 'w'
        with open(file_path, mode) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file {file_path}: {e}")
        return False