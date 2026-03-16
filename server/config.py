from typing import Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ai_provider: Literal["claude", "openai"] = "claude"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"
    openai_model: str = "gpt-4o"

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    max_upload_size_mb: int = 20

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8",
                    "extra": "ignore"}


settings = Settings()
