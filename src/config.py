from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")

    default_model_alias: str = Field(default="openai:gpt-5", alias="DEFAULT_MODEL_ALIAS")
    temperature: float = Field(default=0.2, alias="TEMPERATURE")
    max_tokens: int = Field(default=2000, alias="MAX_TOKENS")
    request_timeout_s: int = Field(default=60, alias="REQUEST_TIMEOUT_S")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
