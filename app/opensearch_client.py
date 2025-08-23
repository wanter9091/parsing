from opensearchpy import OpenSearch
from .config import settings

# 환경변수 설정
from app.config import settings
OS_HOST = settings.OS_HOST

# OpenSearch 접속 정보
os_client = OpenSearch(
    hosts=OS_HOST,# OpenSearch 노드 URL
    http_compress=True,
    retry_on_timeout=True,
    max_retries=3,
    request_timeout=60,
)
