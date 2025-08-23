
from typing import List, Optional
from pydantic import BaseModel, Field, conint


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