# ingest_to_os.py  (기존 ingest_to_es.py 대체)

import os
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
from .parse_xml import parse_darter_xml
import codecs

from app.opensearch_client import os_client

from typing import Dict, Any, Generator

# 파싱 데이터 OpenSearch 인덱스 매핑 정의
from app.models.parsing_schemas import INDEX_MAPPINGS

DOC_CODE_INDEX_MAP = {
    "11013": "rpt_qt", # 분기보고서
    "11012": "rpt_half", # 반기보고서
    "11011": "rpt_biz", # 사업보고서
    "10001": "rpt_sec_eq", # 이건뭐지? 증권신고서인가?
    "00760": "rpt_ad", # 감사보고서
    "00761": "rpt_ad_con", # 감사보고서(연결)
    "99999": "rpt_other",
}



def create_indices():
    """사전 정의 인덱스 생성(있으면 skip)"""
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

def generate_actions(data_dir):
    """디렉터리 하위 XML들을 파싱하고 bulk 액션 생성"""
    root_dirs = ["분기", "반기", "사업", "증권"]

    for folder_name in root_dirs: # 종류별로 시도
        full_dir_path = os.path.join(data_dir, folder_name) #경로를 data_dir/보고서종류로 설정
        if not os.path.isdir(full_dir_path): # 존재하지않으면
            print(f"Directory not found: {full_dir_path}")
            continue

        print(f"Processing directory: {full_dir_path}")
        file_count = 0

        for root, dirs, files in os.walk(full_dir_path): # 해당 경로에 있는 파일 작업 시작
            if file_count >= 10:
                print(f"Reached file limit (10) for folder: {folder_name}. Skipping remaining files.")
                break

            for file_name in files:
                if file_count >= 10:
                    break

                if file_name.endswith(".xml"):
                    file_path = os.path.join(root, file_name) # 해당 경로의 해당 파일로 설정

                    try:
                        with codecs.open(file_path, "r", encoding="utf-8") as f:
                            xml_content = f.read()

                        parsed_data = parse_darter_xml(xml_content, file_name)
                        if parsed_data:
                            doc_code = parsed_data.get("doc_code", "99999")
                            target_index = DOC_CODE_INDEX_MAP.get(doc_code, "rpt_other")

                            yield {
                                "_index": target_index,
                                "_id": parsed_data["doc_id"],
                                "_source": parsed_data,
                            }
                            file_count += 1

                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")
                        continue
    print("All folders have been processed up to the file limit.")

# 하나만 파싱해서 오픈서치에 넣기
def one_parse_xml(file_dict: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    try:
        # 딕셔너리 키에 안전하게 접근합니다.
        xml_content = file_dict.get("content")
        rcept_no = file_dict.get("rcept_no")
        
        # 필수 키가 없는 경우 바로 에러 로그를 출력하고 종료
        if not xml_content or not rcept_no:
            print("Error: Missing 'content' or 'rcept_no' in input dictionary.")
            return

        # XML 파싱
        parsed_data = parse_darter_xml(xml_content, rcept_no)
        
        # 파싱된 데이터가 유효한지 확인
        if parsed_data and parsed_data.get("doc_id"):
            doc_code = parsed_data.get("doc_code", "99999")
            target_index = DOC_CODE_INDEX_MAP.get(doc_code, "rpt_other")

            # OpenSearch에 보낼 데이터를 yield
            yield {
                "_index": target_index,
                "_id": parsed_data["doc_id"],
                "_source": parsed_data,
            }
        else:
            print(f"Warning: No valid data or doc_id parsed from rcept_no '{rcept_no}'.")
    
    except Exception as e:
        print(f"Critical Error during XML parsing for rcept_no '{rcept_no}': {e}")


def main():
    create_indices()

    data_raw_path = "C:/01571107"
    if not os.path.isdir(data_raw_path):
        print(f"Error: The directory '{data_raw_path}' does not exist.")
        return

    print("Starting data ingestion using bulk API...")
    try:
        success, failed = bulk(
            os_client,
            generate_actions(data_raw_path),
            chunk_size=500,
            stats_only=True
        )
        print(f"Bulk ingestion completed. Succeeded: {success}, Failed: {failed}")
    except Exception as e:
        print(f"An error occurred during bulk ingestion: {e}")

if __name__ == "__main__":
    main()
