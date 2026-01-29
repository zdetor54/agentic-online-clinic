"""
Environment variables for the project: read from your .env file.

Uses pydantic-settings to load the environment variables from the .env file.
The prefix matches the prefix in the .env files, and gets only those variables.
The classes should match the structure of the .env file.

The extra="ignore" means that any variables that are not defined in the settings
will be ignored.

The model_config is used to configure the settings.

'env_prefix' is used to specify the prefix for the environment variables. For example:
    Variables that start with GENERAL_ will be mapped to the GeneralSettings class.
    Variables that start with AZURE_ will be mapped to the AzureSettings class.
    etc.
"""

from loguru import logger
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class GeneralSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GENERAL_",
        env_file=".env",
        extra="ignore",
    )

    env: str = "dev"
    debug: bool = False


class AzureSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AZURE_",
        env_file=".env",
        extra="ignore",
    )

    openai_api_key: SecretStr
    openai_endpoint: str
    openai_api_version: str
    location: str


class EnvironmentSettings(BaseSettings):
    """Contains all environment-specific configurations, in one class."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    general: GeneralSettings
    azure: AzureSettings


def get_env_settings(env_file: str = ".env") -> EnvironmentSettings:
    """Get the settings from the environment variables."""
    return EnvironmentSettings.model_construct(
        general=GeneralSettings(_env_file=env_file),  # type: ignore
        azure=AzureSettings(_env_file=env_file),  # type: ignore
    )


# Example usage
if __name__ == "__main__":
    ENV = get_env_settings()
    # print all the env variables
    for key, value in ENV.model_dump().items():
        logger.info(f"{key}: {value}")

    # Azure
    logger.info(f"Azure OpenAI API Key: {ENV.azure.openai_api_key}")
    logger.info(f"Azure OpenAI Endpoint: {ENV.azure.openai_endpoint}")
    logger.info(f"Azure Location: {ENV.azure.location}")
    logger.info(f"Azure OpenAI API Version: {ENV.azure.openai_api_version}")
