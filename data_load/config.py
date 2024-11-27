import logging
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


def get_root_dir() -> Path:
    return Path(__file__).parent.parent.parent.parent


INFO_LOGGING_CONFIG: dict[str, Any] = {
    "level": logging.INFO,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "datefmt": "%d-%b-%y %H:%M:%S",
}

logger = logging.getLogger(__name__)
logging.basicConfig(**INFO_LOGGING_CONFIG)


class Config(BaseSettings):
    OAI_ENDPOINT: str = ""
    OAI_API_KEY: str = ""

    REDIS_URL: str = "redis://localhost:6379"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "postgres"

    model_config = SettingsConfigDict(
        env_prefix="TI_",
        case_sensitive=True,
        env_file=get_root_dir() / ".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    RAW_DATA_FOLDER: Path = get_root_dir() / "data" / "Raw Data"
    PROCESSED_DATA_FOLDER: Path = get_root_dir() / "data" / "Processed Data"
