from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    search_api_key: str = Field(..., alias="SEARCH_API_KEY")
    search_provider: str = Field(default="serper")
    model: str = Field(default="gpt-4o")
    max_docs: int = Field(default=5)

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = AppSettings()  # type: ignore[call-arg]