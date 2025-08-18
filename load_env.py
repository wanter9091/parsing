import os
from dotenv import load_dotenv

load_dotenv()

OPENSEARCH_HOST = [os.getenv("OPENSEARCH_HOST")]
MY_API_BASE_URL = os.getenv("MY_API_BASE_URL")
MY_API_CORE_REPORTS = os.getenv("MY_API_CORE_REPORTS")
DART_API_KEY = os.getenv("DART_API_KEY")