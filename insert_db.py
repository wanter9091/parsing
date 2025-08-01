# insert_db.py
from elasticsearch import Elasticsearch, helpers, exceptions

ES_HOST = "http://localhost:9200"
INDEX_NAME = "rpt_q1"

# 1) 인덱스 settings + mappings (custom analyzer 포함)
INDEX_BODY = {
  "settings": {
    "analysis": {
      "analyzer": {
        "html_lower_analyzer": {
          "tokenizer": "standard",
          "char_filter": ["html_strip"],
          "filter": ["lowercase"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "doc_id":     {"type": "keyword"},
      "doc_name":   {"type": "keyword"},
      "doc_code":   {"type": "keyword"},
      "pub_date":   {"type": "date", "format": "yyyyMMdd"},
      "corp_code":  {"type": "keyword"},
      "corp_name":  {"type": "keyword"},
      "sections": {
        "type": "nested",
        "properties": {
          "sec_id":      {"type": "keyword"},
          "sec_title":   {"type": "text"},
          "sec_content": {"type": "text", "analyzer": "html_lower_analyzer"}
        }
      }
    }
  }
}

def ensure_index(es, name):
    if not es.indices.exists(index=name):
        es.indices.create(index=name, body=INDEX_BODY)

def resolve_doc_id(es, index, doc_id):
    base = doc_id
    suffix = 0
    candidate = base
    while True:
        try:
            # try get doc by ID
            es.get(index=index, id=candidate)
            # exists → increase suffix
            suffix += 1
            candidate = f"{base}_{suffix}"
        except exceptions.NotFoundError:
            return candidate

def bulk_index_reports(es, index, reports):
    actions = []
    for rpt in reports:
        resolved_id = resolve_doc_id(es, index, rpt["doc_id"])
        action = {
            "_index": index,
            "_id": resolved_id,
            "_source": rpt
        }
        actions.append(action)
    resp = helpers.bulk(es, actions, raise_on_error=False)
    return resp

def main(reports, index_name=INDEX_NAME):
    es = Elasticsearch(ES_HOST)
    ensure_index(es, index_name)
    success, errors = bulk_index_reports(es, index_name, reports)
    print(f"Bulk result: success={success}, errors={len(errors)}")
    if errors:
        print("Errors details:", errors)

if __name__ == "__main__":
    # reports 변수 외부에서 준비
    main(reports, index_name="rpt_q1_test")
