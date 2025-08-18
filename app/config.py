from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENSEARCH_HOST: str = "localhost"
    OPENSEARCH_PORT: int = 9200
    OPENSEARCH_USER: str = "admin"
    OPENSEARCH_PASSWORD: str = "admin"
    OPENSEARCH_SCHEME: str = "http"

    OS_HOST : str
    MY_API_BASE_URL : str
    MY_API_CORE_REPORTS : str
    DART_API_KEY : str
    
    class Config:
        env_file = ".env"

settings = Settings()