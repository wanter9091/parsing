from pydantic import BaseModel, Field, conint
from typing import List, Optional
import json
from dataclasses import dataclass
import requests

#압축해제용
import zipfile
import io
from typing import Dict

# OpenSearch 클라이언트
from opensearchpy.helpers import bulk
from opensearchpy import OpenSearch

from app.services.parsing.ingest_to_os_from_xml import one_parse_xml



# OpenSearch 접속 정보
OS_HOSTS = ["http://localhost:9200"]  # OpenSearch 노드 URL
os_client = OpenSearch(
    hosts=OS_HOSTS,
    http_compress=True,
    retry_on_timeout=True,
    max_retries=3,
    request_timeout=60,
)


# 개별 보고서에 대한 모델
class Report(BaseModel):
    rm: str
    corp_code: str
    corp_name: str
    stock_code: Optional[str] = Field(None)  # stock_code는 없을 수도 있으므로 Optional
    corp_cls: str
    report_nm: str
    rcept_no: str
    flr_nm: str
    rcept_dt: str

# 전체 응답 구조에 대한 모델
class ReportListResponse(BaseModel):
    status: str
    message: str
    list: List[Report] = Field(..., alias="list")
    page_no: conint(ge=1)  # 1 이상의 정수
    page_count: int
    total_count: int
    total_page: int

# 내 기업코드로 api에서 보고서 리스트 가져오기(json형태 안에 있음)
def fetch_report_data_with_pydantic(code:str): # 테스트용 "01571107"
    # 파이썬 f-string 문법으로 수정
    url = f"http://localhost:8080/api/dart/reports/core?corp_code={code}"
    response = requests.get(url)
    response.raise_for_status()
    
    json_data = response.json()
    
    # Pydantic 모델을 사용하여 JSON 데이터를 객체로 변환하고 유효성을 검증
    return ReportListResponse(**json_data)
""" 아래처럼 가져옴
{
    "status": "000",
    "message": "정상\n정상\n정상\n정상",
    "list": [
        {
            "rm": "연",
            "corp_code": "00490090",
            "corp_name": "이지케어텍",
            "stock_code": "099750",
            "corp_cls": "K",
            "report_nm": "사업보고서 (2025.03)",
            "rcept_no": "20250618000187",
            "flr_nm": "이지케어텍",
            "rcept_dt": "20250618"
        },
        {
            "rm": "",
            "corp_code": "00490090",
            "corp_name": "이지케어텍",
            "stock_code": "099750",
            "corp_cls": "K",
            "report_nm": "분기보고서 (2025.06)",
            "rcept_no": "20250813000637",
            "flr_nm": "이지케어텍",
            "rcept_dt": "20250813"
        },
        {
            "rm": "",
            "corp_code": "00490090",
            "corp_name": "이지케어텍",
            "stock_code": "099750",
            "corp_cls": "K",
            "report_nm": "분기보고서 (2024.12)",
            "rcept_no": "20250214000274",
            "flr_nm": "이지케어텍",
            "rcept_dt": "20250214"
        },
        {
            "rm": "",
            "corp_code": "00490090",
            "corp_name": "이지케어텍",
            "stock_code": "099750",
            "corp_cls": "K",
            "report_nm": "반기보고서 (2024.09)",
            "rcept_no": "20241112000018",
            "flr_nm": "이지케어텍",
            "rcept_dt": "20241112"
        },
        {
            "rm": "코",
            "corp_code": "00490090",
            "corp_name": "이지케어텍",
            "stock_code": "099750",
            "corp_cls": "K",
            "report_nm": "감사보고서제출              ",
            "rcept_no": "20250618900310",
            "flr_nm": "이지케어텍",
            "rcept_dt": "20250618"
        }
    ],
    "page_no": 1,
    "page_count": 400,
    "total_count": 180,
    "total_page": 1
}
"""



# 접수번호로 파일 다운로드(크롬이 아니라 .zip으로 받음)
def rept_down_by_list(rcept_no: str):
    
    """접수번호로 파일 다운로드"""
    url = f"https://opendart.fss.or.kr/api/document.xml?crtfc_key=4726810cd40e580c803eb6966f1677df83556317&rcept_no={rcept_no}"
    response = requests.get(url)
    response.raise_for_status()
    return response.content

# 압축 해제 기능(파일을 받아서 압축해제하여 dict로 반환)
def extract_zip_file_to_dict(zip_data: bytes) -> Dict[str, str]:
    """
    압축 파일을 해제하고 XML 파일의 이름과 내용을 딕셔너리로 반환합니다.
    { "파일_이름": "XML_내용", ... } 형식입니다.
    """
    xml_files_dict = {}
    
    try:
        zip_buffer = io.BytesIO(zip_data)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            for file_name in zip_file.namelist():
                # 파일 확장자가 '.xml'인 경우에만 처리
                if file_name.endswith('.xml'):
                    with zip_file.open(file_name) as xml_file:
                        try:
                            # 파일을 읽고 UTF-8로 디코딩
                            xml_content = xml_file.read().decode('utf-8')
                            # 딕셔너리에 파일명을 키로, 내용을 값으로 추가
                            xml_files_dict["rcept_no"] = file_name
                            xml_files_dict["content"] = xml_content
                        except UnicodeDecodeError:
                            print(f"경고: {file_name} 파일을 UTF-8로 디코딩할 수 없습니다. 건너뜁니다.")
                            continue
            
            return xml_files_dict

    except zipfile.BadZipFile:
        print("잘못된 ZIP 파일 형식입니다. 바이너리 데이터가 손상되었을 수 있습니다.")
        return {}

# 접수번호로 XML 파일을 파싱하는 함수
def parse_xml_content(rcept_no: str) -> Dict:
    file=rept_down_by_list(rcept_no) # 접수번호로 파일 다운로드
    unzip_file=extract_zip_file_to_dict(file) # 압축 해제
    print(unzip_file)
    
    try: # XML 파일을 파싱하여 OpenSearch에 적재
        success, failed = bulk(
            os_client,
            one_parse_xml(unzip_file),
            chunk_size=500,
            stats_only=True
        )
        print(f"Bulk ingestion completed. Succeeded: {success}, Failed: {failed}")
    except Exception as e:
        print(f"An error occurred during bulk ingestion: {e}")
    
    return success

# 기업코드로 보고서 리스트를 가져오고, 리스트 내의 보고서들을 접수번호로 XML 파일을 다운로드 및 파싱하는 테스트 함수 성공 수만큼 반환
def repots_by_corp_code_parse_xml(corp_code: str):
    report_list = fetch_report_data_with_pydantic(corp_code).list
    
    success_count = 0
    
    for report in report_list:
        success_count += parse_xml_content(report.rcept_no)  # 각 보고서의 접수번호로 XML 파일을 다운로드 및 파싱
        
    return "sueccess: " + str(success_count)
        


def test_service(corp_code: str):
    return repots_by_corp_code_parse_xml(corp_code)  # 기업코드로 보고서 리스트를 가져오고 XML 파일을 파싱하는 함수 호출

