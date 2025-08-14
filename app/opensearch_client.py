from opensearchpy import OpenSearch
from .config import settings

# 보안 비활성화를 위해 verify_certs=False 사용 가능
client = OpenSearch(
    hosts=[{"host": settings.OPENSEARCH_HOST, "port": settings.OPENSEARCH_PORT}],
    http_auth=(settings.OPENSEARCH_USER, settings.OPENSEARCH_PASSWORD),
    scheme=settings.OPENSEARCH_SCHEME,
    verify_certs=False
)
