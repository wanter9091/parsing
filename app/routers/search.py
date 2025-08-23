from fastapi import APIRouter
from pydantic import BaseModel

from app.services.dart_service import test_service
from ..opensearch_client import os_client as client

router = APIRouter()

INDEX_NAME = "test-index"

class Document(BaseModel):
    id: str
    title: str
    content: str
# 보고서 리스트 가져오고 넘기기 
#그걸로 api 전부 가져오기
# 오픈 서치에 넣기

@router.post("/index")
def index_document(doc: Document):
    response = client.index(
        index=INDEX_NAME,
        id=doc.id,
        body={"title": doc.title, "content": doc.content}
    )
    return {"result": response["result"]}

@router.get("/search")
def search_documents(q: str):
    query = {
        "query": {
            "multi_match": {
                "query": q,
                "fields": ["title", "content"]
            }
        }
    }
    response = client.search(index=INDEX_NAME, body=query)
    hits = [hit["_source"] for hit in response["hits"]["hits"]]
    return {"hits": hits}

@router.get("/test/{corp_code}")
def test(corp_code: str):
    return test_service(corp_code)