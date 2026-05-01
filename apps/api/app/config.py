from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    SUPABASE_URL: str
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_SECRET_KEY: str

    EDGE_KEY_PEPPER: str = "dev-pepper-replace-me"
    DEV_MOCK_AUTH: bool = Field(default=False)
    JWT_AUDIENCE: str = "authenticated"
    JWT_ISSUER_PATH: str = "/auth/v1"

    @property
    def jwks_url(self) -> str:
        return f"{self.SUPABASE_URL.rstrip('/')}{self.JWT_ISSUER_PATH}/.well-known/jwks.json"

    @property
    def jwt_issuer(self) -> str:
        return f"{self.SUPABASE_URL.rstrip('/')}{self.JWT_ISSUER_PATH}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
