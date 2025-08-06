import os
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from parse_pdf import parse_pdf
import json
import codecs

# ElasticSearch 접속 정보
ES_HOSTS = ["http://localhost:9200"] 
es = Elasticsearch(hosts=ES_HOSTS)
# 인덱스 매핑 정의
INDEX_MAPPINGS = {
    "standard": {
        "mappings": {
            "properties": {
                "chap_id": {"type": "keyword"},
                "chap_name": {"type": "keyword"},
                "sec_id": {"type": "keyword"},
                "sec_name": {"type": "keyword"},
                "art_id": {"type": "keyword"},
                "art_name": {"type": "keyword"},
                "content": {"type": "text"},
            },
        },
    },
}


def create_indices():
    """
    미리 정의된 인덱스들을 생성하고 매핑을 적용합니다.
    이미 존재하면 무시합니다.
    """
    for index_name, mapping in INDEX_MAPPINGS.items():
        if not es.indices.exists(index=index_name):
            print(f"Creating index '{index_name}' with mapping...")

            # settings와 mappings를 분리하여 body를 구성
            body = {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    **mapping.get("settings", {}),
                },
                "mappings": mapping.get("mappings", {}),
            }

            es.indices.create(index=index_name, body=body)
        else:
            print(f"Index '{index_name}' already exists.")

def generate_actions(index_name, parsed_data):
    """
    벌크 인서트에 필요한 액션 리스트를 생성합니다.
    """
    for doc in parsed_data:
        yield {
            "_index": index_name,
            "_source": doc,
        }

def ingest_documents(index_name, documents):
    """
    파싱된 문서를 ElasticSearch에 bulk API를 이용해 인제스트합니다.
    """
    if not documents:
        print("No documents to ingest.")
        return
        
    print(f"{len(documents)} documents to ingest into '{index_name}'...")
    success, failed = bulk(es, generate_actions(index_name, documents))
    
    if success:
        print(f"Successfully ingested {success} documents.")
    if failed:
        print(f"Failed to ingest {len(failed)} documents. First error: {failed[0]['index']['error']['reason']}")


if __name__ == "__main__":
    create_indices()
    
    # 파싱할 PDF 파일 경로 설정
    pdf_file_path = "./standard/(붙임4) 기업공시서식 작성기준(2025.6.30. 시행).pdf"
    
    if os.path.exists(pdf_file_path):
        print(f"Parsing PDF file: {pdf_file_path}")
        parsed_result = parse_pdf(pdf_file_path)
        
        if parsed_result:
            # 파싱된 결과를 ElasticSearch에 인제스트
            ingest_documents("standard", parsed_result)
        else:
            print("No data parsed from the PDF.")
    else:
        print(f"Error: The specified PDF file does not exist at {pdf_file_path}")