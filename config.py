from functools import lru_cache

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/daia_academy"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Railway provides postgresql:// but asyncpg requires postgresql+asyncpg://
        if self.DATABASE_URL.startswith("postgresql://"):
            object.__setattr__(self, "DATABASE_URL", self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1))

    # JWT (shared secret with DAIA main API)
    JWT_SECRET_KEY: str = "your-shared-secret-key"
    JWT_ALGORITHM: str = "HS256"

    # Internal DAIA API (for user profile fetches)
    DAIA_API_BASE_URL: str = "https://api.daia.com"
    DAIA_INTERNAL_TOKEN: str = "internal-service-token"

    INTERNAL_SECRET: str = ""

    # Supabase Storage
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_POSTS_BUCKET: str = "posts"

    # App
    APP_ENV: str = "development"
    DEBUG: bool = True
    SQL_ECHO: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
