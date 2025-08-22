# ingest_to_os_from_pdf.py

import os
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
from parse_pdf import parse_pdf

# 인덱스 매핑 정의
from app.config import INDEX_MAPPINGS

# OpenSearch 접속 정보
OS_HOSTS = ["http://localhost:9200"]
os_client = OpenSearch(
    hosts=OS_HOSTS,
    http_compress=True,
    retry_on_timeout=True,
    max_retries=3,
    request_timeout=60,
)

def create_indices():
    """
    미리 정의된 인덱스들을 생성하고 매핑을 적용합니다.
    이미 존재하면 무시합니다.
    """
    for index_name, mapping in INDEX_MAPPINGS.items():
        if not os_client.indices.exists(index=index_name):
            print(f"Creating index '{index_name}' with mapping...")
            body = {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    **mapping.get("settings", {}),
                },
                "mappings": mapping.get("mappings", {}),
            }
            os_client.indices.create(index=index_name, body=body)
        else:
            print(f"Index '{index_name}' already exists.")

def generate_actions(index_name, parsed_data):
    """
    벌크 인서트에 필요한 액션 제너레이터를 생성합니다.
    """
    for doc in parsed_data:
        yield {
            "_index": index_name,
            "_source": doc,
        }

def ingest_documents(index_name, documents):
    """
    파싱된 문서를 OpenSearch에 bulk API로 인제스트합니다.
    """
    if not documents:
        print("No documents to ingest.")
        return

    print(f"{len(documents)} documents to ingest into '{index_name}'...")
    # bulk()는 (성공개수, 에러목록) 튜플을 반환합니다.
    success, errors = bulk(
        os_client,
        generate_actions(index_name, documents),
        refresh=False,            # 필요 시 True
        request_timeout=60,
    )
    print(f"Successfully ingested {success} documents.")
    if errors:
        # errors는 per-item 에러 목록
        print(f"Failed to ingest {len(errors)} documents. First error: {errors[0]}")

if __name__ == "__main__":
    create_indices()

    # 파싱할 PDF 파일 경로 설정
    pdf_file_path = "./standard/(붙임4) 기업공시서식 작성기준(2025.6.30. 시행).pdf"

    if os.path.exists(pdf_file_path):
        print(f"Parsing PDF file: {pdf_file_path}")
        parsed_result = parse_pdf(pdf_file_path)

        if parsed_result:
            ingest_documents("standard", parsed_result)
        else:
            print("No data parsed from the PDF.")
    else:
        print(f"Error: The specified PDF file does not exist at {pdf_file_path}")
