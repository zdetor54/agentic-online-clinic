from src.core.config import Config
from src.core.env import get_env_settings


def test_config():
    """Test that the config can be loaded"""
    Config.from_yaml("configs/config.yaml")


def test_env_settings():
    """Test that the environment settings can be loaded from the .env.example file"""
    get_env_settings(".env.example")
