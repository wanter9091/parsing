import aspose.cells
from aspose.cells import Workbook
# utf-8 인코딩으로 XML 파일을 읽고, 테이블을 마크다운으로 변환하는 스크립트
import re
workbook = Workbook("20240430000817.xml")

workbook.save("20240430000817.md")