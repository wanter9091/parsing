# ingest_to_es.py

import os
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from parse_1q import parse_darter_xml  # 제공된 파싱 스크립트 모듈 임포트
import json
import codecs

# ElasticSearch 접속 정보
ES_HOSTS = ["http://localhost:9200"]  # ElasticSearch 서버 URL 및 포트
es = Elasticsearch(hosts=ES_HOSTS)

# doc_code와 인덱스명을 짝짓는 더미 딕셔너리
# 실제 doc_code에 따라 이 부분을 채워주세요.
DOC_CODE_INDEX_MAP = {
    "11013": "rpt_qt",  # 분기보고서 (1분기, 3분기)
    "11012": "rpt_half",  # 반기보고서
    "11011": "rpt_biz",  # 사업보고서
    "10001": "rpt_sec_eq",  # 증권신고서 (지분증권)
    # 다른 doc_code와 인덱스 매핑을 여기에 추가
    "99999": "rpt_other",  # 기타 보고서 (예외 처리용)
}

# 인덱스별 매핑 설정 (제공된 예시를 기반으로 수정)
# 여기서는 모든 인덱스가 동일한 매핑을 사용한다고 가정합니다.
# 만약 각 인덱스별로 다른 매핑을 사용하고 싶다면, 아래 딕셔너리를 확장하여 사용하세요.
INDEX_MAPPINGS = {
    "rpt_qt": {
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_html_strip_analyzer": {
                        "char_filter": ["html_strip"],
                        "tokenizer": "standard",
                        "filter": ["lowercase"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "doc_name": {"type": "keyword"},
                "doc_code": {"type": "keyword"},
                "pub_date": {"type": "date", "format": "yyyyMMdd"},
                "corp_code": {"type": "keyword"},
                "corp_name": {"type": "keyword"},
                "sections": {
                    "type": "nested",
                    "properties": {
                        "sec_id": {"type": "keyword"},
                        "sec_title": {"type": "text"},
                        "sec_content": {
                            "type": "text",
                            "analyzer": "my_html_strip_analyzer",
                        },
                    },
                },
            }
        },
    },
    "rpt_half": {
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_html_strip_analyzer": {
                        "char_filter": ["html_strip"],
                        "tokenizer": "standard",
                        "filter": ["lowercase"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "doc_name": {"type": "keyword"},
                "doc_code": {"type": "keyword"},
                "pub_date": {"type": "date", "format": "yyyyMMdd"},
                "corp_code": {"type": "keyword"},
                "corp_name": {"type": "keyword"},
                "sections": {
                    "type": "nested",
                    "properties": {
                        "sec_id": {"type": "keyword"},
                        "sec_title": {"type": "text"},
                        "sec_content": {
                            "type": "text",
                            "analyzer": "my_html_strip_analyzer",
                        },
                    },
                },
            }
        },
    },
    "rpt_biz": {
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_html_strip_analyzer": {
                        "char_filter": ["html_strip"],
                        "tokenizer": "standard",
                        "filter": ["lowercase"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "doc_name": {"type": "keyword"},
                "doc_code": {"type": "keyword"},
                "pub_date": {"type": "date", "format": "yyyyMMdd"},
                "corp_code": {"type": "keyword"},
                "corp_name": {"type": "keyword"},
                "sections": {
                    "type": "nested",
                    "properties": {
                        "sec_id": {"type": "keyword"},
                        "sec_title": {"type": "text"},
                        "sec_content": {
                            "type": "text",
                            "analyzer": "my_html_strip_analyzer",
                        },
                    },
                },
            }
        },
    },
    "rpt_sec_eq": {
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_html_strip_analyzer": {
                        "char_filter": ["html_strip"],
                        "tokenizer": "standard",
                        "filter": ["lowercase"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "doc_name": {"type": "keyword"},
                "doc_code": {"type": "keyword"},
                "pub_date": {"type": "date", "format": "yyyyMMdd"},
                "corp_code": {"type": "keyword"},
                "corp_name": {"type": "keyword"},
                "sections": {
                    "type": "nested",
                    "properties": {
                        "sec_id": {"type": "keyword"},
                        "sec_title": {"type": "text"},
                        "sec_content": {
                            "type": "text",
                            "analyzer": "my_html_strip_analyzer",
                        },
                    },
                },
            }
        },
    },
    "rpt_other": {
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_html_strip_analyzer": {
                        "char_filter": ["html_strip"],
                        "tokenizer": "standard",
                        "filter": ["lowercase"],
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "doc_name": {"type": "keyword"},
                "doc_code": {"type": "keyword"},
                "pub_date": {"type": "date", "format": "yyyyMMdd"},
                "corp_code": {"type": "keyword"},
                "corp_name": {"type": "keyword"},
                "sections": {
                    "type": "nested",
                    "properties": {
                        "sec_id": {"type": "keyword"},
                        "sec_title": {"type": "text"},
                        "sec_content": {
                            "type": "text",
                            "analyzer": "my_html_strip_analyzer",
                        },
                    },
                },
            }
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


def generate_actions(data_dir):
    """
    주어진 디렉터리 경로를 순회하며 XML 파일을 파싱하고
    Elasticsearch bulk API를 위한 액션 제너레이터를 반환합니다.
    """
    root_dirs = ["1분기", "3분기", "반기", "사업", "증권"]

    for folder_name in root_dirs:
        full_dir_path = os.path.join(data_dir, folder_name)
        if not os.path.isdir(full_dir_path):
            print(f"Directory not found: {full_dir_path}")
            continue

        print(f"Processing directory: {full_dir_path}")

        # os.walk를 사용하여 하위 폴더와 파일 모두 탐색
        for root, dirs, files in os.walk(full_dir_path):
            for file_name in files:
                if file_name.endswith(".xml"):
                    file_path = os.path.join(root, file_name)
                    doc_id = os.path.splitext(file_name)[0]

                    # 'doc_id/doc_id.xml' 형태의 파일만 처리
                    if os.path.basename(root) != doc_id or file_name != f"{doc_id}.xml":
                        print(f"Skipping non-primary XML file: {file_path}")
                        # doc_id 폴더 안에 있는 추가 xml 파일을 처리하고 싶다면, 이 부분을 수정하세요
                        # 예를 들어, doc_id가 아닌 다른 이름의 xml 파일을 처리하는 로직을 추가할 수 있습니다.
                        # continue
                        # 임시로 이 부분은 주석처리하여 모든 xml파일을 파싱하도록 합니다.
                        pass

                    try:
                        with codecs.open(file_path, "r", encoding="utf-8") as f:
                            xml_content = f.read()

                        parsed_data = parse_darter_xml(xml_content, file_name)

                        if parsed_data:
                            doc_code = parsed_data.get("doc_code", "99999")
                            target_index = DOC_CODE_INDEX_MAP.get(doc_code, "rpt_other")

                            # Bulk API를 위한 액션 생성
                            action = {
                                "_index": target_index,
                                "_id": parsed_data["doc_id"],
                                "_source": parsed_data,
                            }
                            yield action

                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")
                        continue


def main():
    """
    메인 함수: 인덱스 생성 및 데이터 주입 프로세스 실행
    """
    # 1. 인덱스 및 매핑 생성
    create_indices()

    # 2. 데이터 파일 경로 설정
    data_raw_path = "./report"
    if not os.path.isdir(data_raw_path):
        print(f"Error: The directory '{data_raw_path}' does not exist.")
        return

    # 3. Bulk API를 사용하여 데이터 주입
    print("Starting data ingestion using bulk API...")
    try:
        success, failed = bulk(es, generate_actions(data_raw_path), stats_only=True)
        print(f"Bulk ingestion completed. Succeeded: {success}, Failed: {failed}")
    except Exception as e:
        print(f"An error occurred during bulk ingestion: {e}")


if __name__ == "__main__":
    main()
