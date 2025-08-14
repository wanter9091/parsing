from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DB_URL = "mysql+pymysql://testuser:pass1234@localhost:3310/testdb"
engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
#-----------------------------------------------------------------------------------------
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