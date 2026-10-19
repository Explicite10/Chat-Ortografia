from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b-instruct"
    max_chars: int = 2000
    ollama_timeout: float = 60.0


settings = Settings()
