from functools import lru_cache

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/daia_academy"

    # JWT (shared secret with DAIA main API)
    JWT_SECRET_KEY: str = "your-shared-secret-key"
    JWT_ALGORITHM: str = "HS256"

    # Internal DAIA API (for user profile fetches)
    DAIA_API_BASE_URL: str = "https://api.daia.com"
    DAIA_INTERNAL_TOKEN: str = "internal-service-token"

    INTERNAL_SECRET: str         

    # App
    APP_ENV: str = "development"
    DEBUG: bool = True
    SQL_ECHO: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
