from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class AppSettings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    search_api_key: str = Field(..., alias="SEARCH_API_KEY")
    search_provider: str = Field(default="serper")
    model: str = Field(default="gpt-4o")
    max_docs: int = Field(default=5)
    dedupe_threshold : int = Field(default=75)
    
    # Concurrency limits
    fetch_concurrency_limit: int = Field(default=10)
    extract_concurrency_limit: int = Field(default=5)


settings = AppSettings()  # type: ignore[call-arg]
