import os
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    app_name: str = "RhythmIQ Admin Monitor"
    app_env: str = "dev"
    database_url: str = f"sqlite:///{os.path.join(BASE_DIR, 'rhythm_iq.db')}"
    secret_key: str = "supersecretjwtkeychangeit"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    model_storage_dir: str = os.path.join(BASE_DIR, "models")

    tracker_service_enabled: bool = True
    tracker_service_url: str = "http://localhost:3001"
    tracker_service_timeout_seconds: int = 20
    tracker_service_platforms: str = "whatsapp,signal"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        protected_namespaces=("settings_",),
    )


settings = Settings()
