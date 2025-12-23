# Loads configuration settings from a .env file for the application.
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Defines the application's configuration variables.
class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Look for the .env file in the Backend root directory (3 levels up from src/core/config.py)
    model_config = SettingsConfigDict(env_file=str(Path(__file__).parent.parent.parent / '.env'), extra='ignore')

settings = Settings()
