# main.py
import os, json, time, random
from parse_1q import parse_darter_xml
from insert_db import INDEX_BODY, resolve_doc_id
from elasticsearch import Elasticsearch, helpers

ES_HOST = "http://localhost:9200"
REPORT_ROOT = "./report/1분기"
INDEX_NAME = "rpt_q1"
BATCH_SIZE = 500
LOG_FAIL_PATH = "failed_docs.log"

def init_index(es):
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(index=INDEX_NAME, body=INDEX_BODY)
    # permanent replica=0 and no refresh
    es.indices.put_settings(index=INDEX_NAME, body={
        "index": {
            "number_of_replicas": 0,
            "refresh_interval": "-1"
        }
    })

def get_xml_paths(root):
    for doc in os.listdir(root):
        path = os.path.join(root, doc, f"{doc}.xml")
        if os.path.isfile(path):
            yield path

def get_random_10_paths(root):
    folders = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
    selected = random.sample(folders, min(10, len(folders)))
    return [os.path.join(root, doc, f"{doc}.xml") for doc in selected]

def write_fail(doc_id, reason, data=None):
    with open(LOG_FAIL_PATH, "a", encoding="utf-8") as f:
        f.write(f"{time.asctime()} | {doc_id} | {reason} | {json.dumps(data or {}, ensure_ascii=False)}\n")

def index_batch(es, docs):
    actions = []
    for rpt in docs:
        _id = resolve_doc_id(es, INDEX_NAME, rpt["doc_id"])
        actions.append({"_index": INDEX_NAME, "_id": _id, "_source": rpt})
    resp = helpers.bulk(es, actions, raise_on_error=False, refresh=False, wait_for_active_shards=1)
    return resp

def run():
    es = Elasticsearch(ES_HOST)
    init_index(es)
    buffer=[]; total=0

    # for path in get_xml_paths(REPORT_ROOT):
    for path in get_random_10_paths(REPORT_ROOT):
        doc_id = os.path.basename(path).split(".")[0]
        try:
            content = open(path, encoding="utf-8").read()
            parsed = parse_darter_xml(content, os.path.basename(path))
            if not parsed: raise ValueError("파싱 오류")
            print(f"XML 파싱 성공: {doc_id}.xml")
        except Exception as e:
            write_fail(doc_id, f"파싱 오류: {e}")
            continue

        buffer.append(parsed)
        if len(buffer)>=BATCH_SIZE:
            success, errors = index_batch(es, buffer)
            total += success
            for err in errors:
                did = err.get("index",{}).get("data",{}).get("doc_id","")
                write_fail(did, f"인덱싱 실패: {err}")
            buffer=[]

    if buffer:
        success, errors = index_batch(es, buffer)
        total += success
        for err in errors:
            did = err.get("index",{}).get("data",{}).get("doc_id","")
            write_fail(did, f"인덱싱 실패: {err}")

    print(f"총 성공: {total}, 실패 기록: {LOG_FAIL_PATH}")

if __name__=="__main__":
    run()
