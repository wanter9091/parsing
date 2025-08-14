from fastapi import APIRouter
from pydantic import BaseModel
from ..opensearch_client import client

router = APIRouter()

INDEX_NAME = "test-index"

class Document(BaseModel):
    id: str
    title: str
    content: str

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
