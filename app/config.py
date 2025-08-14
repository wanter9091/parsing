from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENSEARCH_HOST: str = "localhost"
    OPENSEARCH_PORT: int = 9200
    OPENSEARCH_USER: str = "admin"
    OPENSEARCH_PASSWORD: str = "admin"
    OPENSEARCH_SCHEME: str = "http"

    class Config:
        env_file = ".env"

settings = Settings()
