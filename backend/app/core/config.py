from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"


class Settings(BaseSettings):
    app_name: str = Field(default="CommCoach AI API", alias="APP_NAME")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    sql_echo: bool = Field(default=False, alias="SQL_ECHO")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    database_url: str = Field(default="sqlite+aiosqlite:///./commcoach.db", alias="DATABASE_URL")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    allowed_origins: str = Field(default="http://localhost:3000", alias="ALLOWED_ORIGINS")
    uploads_dir: str = Field(default="uploads", alias="UPLOADS_DIR")
    reports_dir: str = Field(default="reports", alias="REPORTS_DIR")
    max_upload_size_mb: int = Field(default=150, alias="MAX_UPLOAD_SIZE_MB")
    transcription_model_size: str = Field(default="small", alias="TRANSCRIPTION_MODEL_SIZE")
    transcription_device: str = Field(default="cpu", alias="TRANSCRIPTION_DEVICE")
    transcription_compute_type: str = Field(default="int8", alias="TRANSCRIPTION_COMPUTE_TYPE")
    transcription_batch_size: int = Field(default=4, alias="TRANSCRIPTION_BATCH_SIZE")
    audio_sample_rate: int = Field(default=16000, alias="AUDIO_SAMPLE_RATE")
    video_analysis_sample_interval_seconds: float = Field(
        default=1.0, alias="VIDEO_ANALYSIS_SAMPLE_INTERVAL_SECONDS"
    )
    interview_llm_temperature: float = Field(default=0.1, alias="INTERVIEW_LLM_TEMPERATURE")
    interview_llm_timeout_seconds: float = Field(
        default=120.0, alias="INTERVIEW_LLM_TIMEOUT_SECONDS"
    )
    grammar_llm_timeout_seconds: float = Field(
        default=60.0, alias="GRAMMAR_LLM_TIMEOUT_SECONDS"
    )
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_base_url: str = Field(
        default="https://api.groq.com/openai/v1", alias="GROQ_BASE_URL"
    )
    groq_model: str = Field(
        default="openai/gpt-oss-120b", alias="GROQ_MODEL"
    )
    chroma_persist_directory: str = Field(default="chroma", alias="CHROMA_PERSIST_DIRECTORY")
    chroma_collection: str = Field(default="commcoach-memory", alias="CHROMA_COLLECTION")
    embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5", alias="EMBEDDING_MODEL"
    )
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")

    model_config = SettingsConfigDict(
        env_file=(
            str(PROJECT_ROOT / ".env"),
            str(BACKEND_DIR / ".env"),
            str(BACKEND_DIR / ".env.secrets"),
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def uploads_dir_path(self) -> Path:
        uploads_path = Path(self.uploads_dir)
        return uploads_path if uploads_path.is_absolute() else PROJECT_ROOT / uploads_path

    @property
    def reports_dir_path(self) -> Path:
        reports_path = Path(self.reports_dir)
        return reports_path if reports_path.is_absolute() else PROJECT_ROOT / reports_path

    @property
    def chroma_persist_directory_path(self) -> Path:
        chroma_path = Path(self.chroma_persist_directory)
        return chroma_path if chroma_path.is_absolute() else PROJECT_ROOT / chroma_path

    @field_validator("debug", mode="before")
    @classmethod
    def coerce_debug_value(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on", "debug"}
        return bool(value)

    @field_validator("sql_echo", mode="before")
    @classmethod
    def coerce_sql_echo_value(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on", "debug"}
        return bool(value)

    @field_validator("max_upload_size_mb", mode="before")
    @classmethod
    def coerce_max_upload_size(cls, value: object) -> int:
        if isinstance(value, int):
            return max(value, 1)
        if isinstance(value, str) and value.strip().isdigit():
            return max(int(value.strip()), 1)
        return 150

    @field_validator("audio_sample_rate", mode="before")
    @classmethod
    def coerce_audio_sample_rate(cls, value: object) -> int:
        if isinstance(value, int):
            return max(value, 8000)
        if isinstance(value, str) and value.strip().isdigit():
            return max(int(value.strip()), 8000)
        return 16000

    @field_validator("transcription_batch_size", mode="before")
    @classmethod
    def coerce_transcription_batch_size(cls, value: object) -> int:
        if isinstance(value, int):
            return max(value, 1)
        if isinstance(value, str) and value.strip().isdigit():
            return max(int(value.strip()), 1)
        return 4

    @field_validator("video_analysis_sample_interval_seconds", mode="before")
    @classmethod
    def coerce_video_analysis_interval(cls, value: object) -> float:
        if isinstance(value, (int, float)):
            return max(float(value), 0.25)
        if isinstance(value, str):
            try:
                return max(float(value.strip()), 0.25)
            except ValueError:
                return 1.0
        return 1.0

    @field_validator("interview_llm_temperature", mode="before")
    @classmethod
    def coerce_interview_llm_temperature(cls, value: object) -> float:
        if isinstance(value, (int, float)):
            return min(max(float(value), 0.0), 1.0)
        if isinstance(value, str):
            try:
                return min(max(float(value.strip()), 0.0), 1.0)
            except ValueError:
                return 0.1
        return 0.1

    @field_validator("interview_llm_timeout_seconds", mode="before")
    @classmethod
    def coerce_interview_llm_timeout(cls, value: object) -> float:
        if isinstance(value, (int, float)):
            return max(float(value), 5.0)
        if isinstance(value, str):
            try:
                return max(float(value.strip()), 5.0)
            except ValueError:
                return 45.0
        return 45.0

    @field_validator("grammar_llm_timeout_seconds", mode="before")
    @classmethod
    def coerce_grammar_llm_timeout(cls, value: object) -> float:
        if isinstance(value, (int, float)):
            return max(float(value), 5.0)
        if isinstance(value, str):
            try:
                return max(float(value.strip()), 5.0)
            except ValueError:
                return 60.0
        return 60.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
