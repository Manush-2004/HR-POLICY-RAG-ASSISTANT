"""Application configuration managed via Pydantic Settings."""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory is the backend root directory (parent of hr_assistant)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Central configuration for backend application and RAG pipeline."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Google Gemini LLM
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    # Jina Embeddings
    jina_api_key: Optional[str] = Field(default=None, alias="JINA_API_KEY")
    jina_model: str = Field(default="jina-embeddings-v2-base-en", alias="JINA_MODEL")

    # Document & Vector Storage
    hr_policy_path: Path = Field(
        default=BASE_DIR / "data" / "hr_policy.pdf",
        alias="HR_POLICY_PATH",
    )
    chroma_persist_directory: Path = Field(
        default=BASE_DIR / "data" / "store",
        alias="CHROMA_PERSIST_DIRECTORY",
    )

    # RAG Chunking and Retrieval Settings
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    top_k: int = Field(default=3, alias="TOP_K")

    # Frontend CORS & Network
    frontend_origin: str = Field(
        default="http://localhost:5173",
        alias="FRONTEND_ORIGIN",
    )
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    @property
    def effective_google_api_key(self) -> Optional[str]:
        """Return GOOGLE_API_KEY if present, falling back to GEMINI_API_KEY."""
        return self.google_api_key or self.gemini_api_key

    def resolve_hr_policy_path(self) -> Path:
        """Resolve policy PDF path to an absolute path relative to BASE_DIR if needed."""
        if self.hr_policy_path.is_absolute():
            return self.hr_policy_path
        return BASE_DIR / self.hr_policy_path

    def resolve_chroma_persist_directory(self) -> Path:
        """Resolve Chroma persist dir to an absolute path relative to BASE_DIR if needed."""
        if self.chroma_persist_directory.is_absolute():
            return self.chroma_persist_directory
        return BASE_DIR / self.chroma_persist_directory


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Singleton getter for application settings."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
