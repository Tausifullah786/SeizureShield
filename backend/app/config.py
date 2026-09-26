"""Central configuration, loaded once from the .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    mongodb_url: str
    database_name: str = "seizureshield"

    # Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440          # 24 hours

    # Google OAuth (optional — leave blank to disable Google login)
    google_client_id: str = ""

    # Machine learning
    model_path: str = "trained_models/bilstm_seizure_model.pth"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),   # allows a field named model_path
    )


settings = Settings()