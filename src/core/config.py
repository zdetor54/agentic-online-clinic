"""
Config class for the project, which reads the config/config.yaml file.

Any update to the config.yaml file should be reflected here.

Uses pydantic for complex validation, and dataclasses for simple validation.
Freezes the configs, so it can't be changed after loading for safety.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class GeneralConfig:
    """Contains general configuration for the project."""

    name: str
    logo_type: Literal["colour", "white"] = "colour"
    random_state: int = 42


@dataclass(frozen=True)
class PathsConfig:
    """Contains paths for the project."""

    data: Path = Path("data")
    logs: Path = Path("logs")
    plots: Path = Path("plots")
    rag_index: Path = Path("rag_index")


@dataclass(frozen=True)
class MLConfig:
    """Contains configuration for machine learning models."""

    train_test_split: float
    model_name: str
    model_params: dict


class LLMConfig(BaseModel):
    """Contains configuration for large language models / RAG"""

    model_name: str
    embedding_model_name: str
    temperature: float = Field(..., ge=0, le=1, description="Must be between 0 and 1")
    chunk_size: int = Field(..., description="Chunk size for the model")
    retrieval_k: int = Field(..., description="Number of documents to retrieve")
    rerank: bool = Field(..., description="Whether to rerank the documents")

    # Freeze pydantic model
    model_config = ConfigDict(frozen=True)


class Config(BaseModel):
    """Contains all configuration for the project, in one class."""

    general: GeneralConfig
    paths: PathsConfig
    llm: LLMConfig
    ml: MLConfig

    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_yaml(cls, path: Path | str) -> "Config":
        with Path(path).open("r") as file:
            data = yaml.safe_load(file)
        logger.debug(f"Successfully loaded configuration from {path}")
        return cls(**data)


# Example usage
if __name__ == "__main__":
    config_path = Path("configs/config.yaml")
    config = Config.from_yaml(config_path)

    logger.info(f"Model Name: {config.llm.model_name}")
    logger.info(f"Temperature: {config.llm.temperature:.2f}")
    logger.info(f"Chunk Size: {config.llm.chunk_size}")
    logger.info(f"Retrieval K: {config.llm.retrieval_k}")
    logger.info(f"Rerank: {config.llm.rerank}")
