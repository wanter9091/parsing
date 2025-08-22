# 인덱스 매핑 정의
INDEX_MAPPINGS = {
    "standard": {
        "mappings": {
            "properties": {
                "chap_id":   {"type": "keyword"},
                "chap_name": {"type": "keyword"},
                "sec_id":    {"type": "keyword"},
                "sec_name":  {"type": "keyword"},
                "art_id":    {"type": "keyword"},
                "art_name":  {"type": "keyword"},
                "content":   {"type": "text"},
            },
        },
    },
}