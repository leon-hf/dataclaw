"""应用配置，支持 .env 文件和环境变量。"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DCLAW_",
    )

    # 应用
    app_name: str = "Dataclaw"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./dataclaw.db"

    # 数据存储
    data_dir: Path = Path("./data")
    artifacts_dir: Path = Path("./data/artifacts")

    # LLM (Agent 判断层)
    llm_provider: str = "openai"  # openai, etc.
    llm_model: str = "gpt-4o"
    llm_api_key: str = ""
    llm_max_calls_per_session: int = 10
    llm_max_input_tokens: int = 100_000
    llm_max_output_tokens: int = 20_000
    llm_timeout_seconds: int = 30

    # S3 / 对象存储（可选）
    s3_endpoint: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "dataclaw"


settings = Settings()
