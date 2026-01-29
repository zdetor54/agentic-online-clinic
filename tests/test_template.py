from ai_cgi_branding import StreamlitUIService

from src.core.config import Config
from src.core.env import get_env_settings


def test_config():
    """Test that the config can be loaded"""
    Config.from_yaml("configs/config.yaml")


def test_env_settings():
    """Test that the environment settings can be loaded from the .env.example file"""
    get_env_settings(".env.example")


def test_branding():
    """Test that the branding works"""
    # Initialise the class
    ui_service = StreamlitUIService()
    ui_service.load_css()

    # Get the logo, make sure there's something there
    assert ui_service.get_logo("colour") is not None
