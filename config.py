# Loads configuration settings from a .env file for the application.
from pydantic_settings import BaseSettings

# Defines the application's configuration variables.
class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        # Specifies the name of the environment file to load.
        env_file = ".env"


settings = Settings()
