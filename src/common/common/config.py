import logging
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

from common.utils import get_root_dir

INFO_LOGGING_CONFIG: dict[str, Any] = {
    "level": logging.INFO,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "datefmt": "%d-%b-%y %H:%M:%S",
}


class Config(BaseSettings):
    OAI_ENDPOINT: str = ""
    OAI_API_KEY: str = ""

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
