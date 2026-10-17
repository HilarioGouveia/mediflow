import os
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME: str = Field(default="gemini-3.5-flash", min_length=1)
    GEMINI_TIMEOUT_MS: int = Field(default=20000, ge=1000, le=60000)
    GEMINI_MAX_ATTEMPTS: int = Field(default=3, ge=1, le=3)
    OCI_CONFIG_FILE: str = os.getenv("OCI_CONFIG_FILE", "~/.oci/config")
    OCI_CONFIG_PROFILE: str = os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")
    STORAGE_MODE: Literal["memory", "emulator", "oci"] = "memory"
    OCI_SERVICE_ENDPOINT: str = "http://localhost:4599"
    OCI_NAMESPACE: str = os.getenv("OCI_NAMESPACE", "mi-tenancy-namespace")
    OCI_BUCKET_NAME: str = os.getenv("OCI_BUCKET_NAME", "mediflow-documentos-clinicos")

    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()


