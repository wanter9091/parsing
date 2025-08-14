from fastapi import FastAPI
from .routers import search

app = FastAPI(title="FastAPI + OpenSearch Example")

app.include_router(search.router, prefix="/search", tags=["Search"])

@app.get("/")
def root():
    return {"message": "FastAPI + OpenSearch running!"}
