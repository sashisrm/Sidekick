from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: str = "development"
    upload_dir: str = "/app/uploads"
    chroma_dir: str = "/app/chroma_db"

    # DB
    database_url: str = "postgresql+asyncpg://sidekick:sidekick_pass@localhost:5432/sidekick_db"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # JWT
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 10080  # 7 days

    # Anthropic
    anthropic_api_key: str = ""

    # Models
    embedding_model: str = "all-MiniLM-L6-v2"
    claude_sonnet_model: str = "claude-sonnet-4-6"
    claude_haiku_model: str = "claude-haiku-4-5-20251001"

    # RAG
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 50
    retrieval_top_k: int = 8
    semantic_candidates: int = 25
    bm25_candidates: int = 25


settings = Settings()
