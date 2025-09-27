from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application settings.
    Pydantic's BaseSettings automatically reads variables from the environment.
    """

    # Define a model configuration to load from a .env file
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Core application settings
    ENVIRONMENT: str = "development"

    # API Keys
    TAVILY_API_KEY: str
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str
    LANGSMITH_API_KEY: str | None = None


# Create a single, importable instance of the settings
settings = Settings()
