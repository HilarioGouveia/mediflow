import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OCI_CONFIG_FILE: str = os.getenv("OCI_CONFIG_FILE", "~/.oci/config")
    OCI_CONFIG_PROFILE: str = os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")
    OCI_NAMESPACE: str = os.getenv("OCI_NAMESPACE", "mi-tenancy-namespace")
    OCI_BUCKET_NAME: str = os.getenv("OCI_BUCKET_NAME", "mediflow-documentos-clinicos")

    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")

    class Config:
        env_file = ".env"


settings = Settings()


