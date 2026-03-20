"""Application configuration via environment variables."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "Análise de Decisões v3"
    debug: bool = False
    cors_origins: str = "*"

    # Database
    database_url: str = "postgresql://analise:analise@localhost:5432/analise_decisoes"

    # JWT Auth
    jwt_secret: str = "CHANGE-ME-IN-PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # Admin
    admin_email: str = "admin@soarespicon.adv.br"
    admin_password: str = "Mudar@123"

    # LLM Providers
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # DataJuri
    datajuri_base_url: str = ""
    datajuri_client_id: str = ""
    datajuri_secret_id: str = ""
    datajuri_username: str = ""
    datajuri_password: str = ""

    # Zion
    zion_db_host: str = ""
    zion_db_user: str = ""
    zion_db_password: str = ""
    zion_db_database: str = ""
    zion_db_port: int = 3306

    # SharePoint
    sharepoint_client_id: str = ""
    sharepoint_client_secret: str = ""
    sharepoint_site_root: str = ""

    # Dossiê
    dossie_enabled: bool = True
    dossie_db_url: str = ""  # sp-zion DB for case_index queries

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
