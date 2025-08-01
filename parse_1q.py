# parse_1q.py
import xml.etree.ElementTree as ET
import re
import os
import json
import codecs
from bs4 import BeautifulSoup


def preprocess_xml_content(xml_string):
    # 허용되는 태그 이름 리스트
    WHITELIST = {
        "DOCUMENT", "DOCUMENT-NAME", "FORMULA-VERSION", "COMPANY-NAME", "SUMMARY",
        "LIBRARY", "BODY", "EXTRACTION", "COVER", "COVER-TITLE",
        "IMAGE", "IMG", "IMG-CAPTION", "SPAN", "P", "A",
        "TR", "TD", "TH", "TE", "TU", "SECTION-1", "SECTION-2", "SECTION-3",
        "TITLE", "TABLE", "TABLE-GROUP", "COLGROUP", "COL", "THEAD",
        "TBODY", "PGBRK", "PART",
    }
    TAG_RE = re.compile(
        r"<(/?)([A-Za-z0-9\-]+)"               # 그룹 1: 슬래시?, 그룹 2: 태그명
        r"([^>]*)"                             # 그룹 3: 속성 등
        r">"
    )
    def repl(m):
        slash, tag, attrs = m.group(1), m.group(2), m.group(3)
        if tag not in WHITELIST:
            # 전체 태그 엔티티 처리
            inner = m.group(0)[1:-1]  # "<...>" 사이 문자열
            return "&lt;" + inner + "&gt;"
        else:
            # 허용된 태그: 속성은 그대로 유지
            return f"<{slash}{tag}{attrs}>"

    # 1. XML 선언 (Processing Instruction) 추출 및 보호
    xml_declaration_match = re.match(r"<\?xml[^>]*\?>\s*", xml_string)
    xml_declaration = ""
    remaining_xml_string = xml_string

    if xml_declaration_match:
        xml_declaration = xml_declaration_match.group(
            0
        )  # 매치된 선언과 뒤따르는 공백 포함
        remaining_xml_string = xml_string[
            xml_declaration_match.end() :
        ]  # 선언 부분 제거

    # 2. 전체 문자열 앞뒤의 공백 및 개행 문자 제거 (XML 선언 제외한 나머지 부분에 적용)
    cleaned_xml_string = remaining_xml_string.strip()

    # 3. XML 1.0 사양에서 허용되지 않는 제어 문자 제거 (ParseError 방지)
    cleaned_xml_string = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned_xml_string
    )

    # 4. 이스케이프되지 않은 '&' 문자를 '&amp;'로 변환
    cleaned_xml_string = re.sub(r"&(?!#|[a-zA-Z]+;)", r"&amp;", cleaned_xml_string)

    # 5. <...> 형태이지만 유효한 XML 태그 이름이 아닌 특정 패턴을 &lt;...&gt;으로 변환
    #    '<', '>' 사이에 한글이 최소 한글자라도 포함된 경우만 전처리
    kor_pattern = re.compile(r"<([^\">]*[가-힣][^\">]*)>")
    cleaned_xml_string = kor_pattern.sub(r"&lt;\1&gt;", cleaned_xml_string)
    cleaned_xml_string = re.sub(r' USERMARK\s*=\s*"[^"]*"', '', cleaned_xml_string)  # USERMARK 제거
    cleaned_xml_string = TAG_RE.sub(repl, cleaned_xml_string)
    cleaned_xml_string =cleaned_xml_string.replace("<<", "<")
    cleaned_xml_string =cleaned_xml_string.replace(">>", ">")
    # 6. 보호했던 XML 선언을 다시 문자열 맨 앞에 추가
    if xml_declaration:
        # 원래 선언 뒤에 공백이나 개행이 있었다면 그것을 유지
        # 새로운 시작 문자열 앞에도 개행을 넣어 줄 맞춤을 시도합니다.
        cleaned_xml_string = xml_declaration + "\n" + cleaned_xml_string.lstrip()

    return cleaned_xml_string


def clean_table_html_for_llm(html_string):
    """
    LLM에 전달하기 위한 테이블 HTML에서 불필요한 레이아웃/스타일 속성을 제거하고
    비표준 태그 (TE, TU)를 표준 TD로 변환합니다.
    ROWSPAN, COLSPAN과 같은 구조 관련 속성은 유지합니다.
    또한, HTML 문자열 내의 불필요한 줄바꿈과 역슬래시를 제거합니다.
    """
    soup = BeautifulSoup(html_string, "html.parser")

    # 불필요한 속성 제거 목록 (소문자로 비교)
    # LLM에게는 불필요하거나 시각적 정보인 속성들
    attrs_to_remove = [
        "width",
        "height",
        "align",
        "valign",
        "aclass",
        "afixtable",
        "acopy",
        "adelete",
        "aupdatecont",
        "acopycol",
        "amovecol",
        "adeletecol",
        "usermark",
        "acode",
        "aunit",
        "aunitvalue",
        "refno",
        "aassocnote",
        "atoc",
        "atocid",
        "adelim",  # DART 특유의 메타데이터 속성들
        "border",
        "frame",
        "rules",  # 요청에 따라 추가
        "style",
        "class",
        "id",  # 일반적으로 HTML에서 불필요한 속성 추가
    ]

    for tag in soup.find_all(True):  # 모든 태그 순회 (자신 포함)
        # 비표준 태그 (TE, TU)를 표준 TD로 변환
        if tag.name == "te" or tag.name == "tu":
            tag.name = "td"

        # 불필요한 속성 제거
        for attr_name in list(tag.attrs.keys()):
            if attr_name.lower() in attrs_to_remove:
                del tag.attrs[attr_name]

    cleaned_html = str(soup)
    # 고객님의 제안대로 순서대로 처리: 줄바꿈 제거 -> 역슬래시 제거 -> 연속 공백 압축
    cleaned_html = cleaned_html.replace("\n", "")  # 모든 줄바꿈 제거
    cleaned_html = cleaned_html.replace('\\', '')  # 모든 역슬래시 제거

    return cleaned_html.strip()  # 최종적으로 앞뒤 공백 제거


def extract_content_recursive(element, collected_items):
    """
    주어진 Element와 그 하위 Element들을 재귀적으로 탐색하여
    BORDER="1"인 TABLE은 HTML로 (정제 후), 그 외의 텍스트는 일반 텍스트로 collected_items에 추가합니다.
    """
    # BORDER="1"인 TABLE을 발견하면 HTML로 추출하고 이 가지의 탐색은 중단
    if element.tag == "TABLE" and element.get("BORDER") == "1":
        table_html = ET.tostring(element, encoding="utf-8").decode("utf-8").strip()
        cleaned_table_html = clean_table_html_for_llm(
            table_html
        )  # LLM을 위해 HTML 정제
        collected_items.append(
            {"type": "table", "content": cleaned_table_html}
        )  # 타입 추가
        return

    # 현재 엘리먼트의 직접적인 텍스트 노드 처리
    if element.text and element.text.strip():
        # 텍스트 내부의 여러 공백(개행 포함)을 단일 공백으로 정규화
        normalized_text = re.sub(r"\s+", " ", element.text.strip())
        if normalized_text:  # 비어있지 않은 경우에만 추가
            collected_items.append({"type": "text", "content": normalized_text})

    # 자식 엘리먼트들을 재귀적으로 탐색
    for child in element:
        extract_content_recursive(child, collected_items)

        # 자식 엘리먼트의 tail 텍스트 노드 처리
        if child.tail and child.tail.strip():
            # tail 텍스트 내부의 여러 공백(개행 포함)을 단일 공백으로 정규화
            normalized_tail_text = re.sub(r"\s+", " ", child.tail.strip())
            if normalized_tail_text:  # 비어있지 않은 경우에만 추가
                collected_items.append(
                    {"type": "text", "content": normalized_tail_text}
                )


def parse_darter_xml(xml_content, file_name):
    """
    DART 공시보고서 XML 내용을 파싱하고 주요 정보를 추출합니다.
    """
    processed_xml_content = preprocess_xml_content(xml_content)

    try:
        root = ET.fromstring(processed_xml_content)
    except ET.ParseError as e:
        print(f"XML 파싱 오류 발생: {e}")
        error_line_num_1_based = e.position[0]
        error_column_1_based = e.position[1]
        lines = processed_xml_content.splitlines()
        start_line_index = max(0, error_line_num_1_based - 1 - 5)
        end_line_index = min(len(lines), error_line_num_1_based - 1 + 5 + 1)
        print(f"오류 발생: {error_line_num_1_based}행 {error_column_1_based}열")
        for i in range(start_line_index, end_line_index):
            if 0 <= i < len(lines):
                line_num = i + 1
                line_content = lines[i]
                prefix = ">>>" if line_num == error_line_num_1_based else "   "
                print(f"{prefix} {line_num:4d}: {line_content}")
                if line_num == error_line_num_1_based:
                    line_prefix_for_pointer = line_content[: error_column_1_based - 1]
                    tab_corrected_length = len(
                        line_prefix_for_pointer.replace("\t", "    ")
                    )
                    print(f"       {' ' * tab_corrected_length}^")
        return None

    # 최상위 레벨 데이터 추출
    doc_id = file_name.split(".")[0]
    pub_date = file_name[:8]

    doc_name_element = root.find("DOCUMENT-NAME")
    doc_name = doc_name_element.text.strip() if doc_name_element is not None else ""
    doc_code = doc_name_element.get("ACODE") if doc_name_element is not None else ""

    company_name_element = root.find("COMPANY-NAME")
    corp_code = (
        company_name_element.get("AREGCIK") if company_name_element is not None else ""
    )
    corp_name = (
        company_name_element.text.strip() if company_name_element is not None else ""
    )

    report_data = {
        "doc_id": doc_id,
        "doc_name": doc_name,
        "doc_code": doc_code,
        "pub_date": pub_date,
        "corp_code": corp_code,
        "corp_name": corp_name,
        "sections": [],
    }

    section1_elements = root.findall(".//SECTION-1")

    for idx, section1_element in enumerate(section1_elements):
        section_data = {
            "sec_id": None,
            "sec_title": "제목 없음",
            "sec_content": "",  # 최종적으로 합쳐질 문자열
        }

        title_element = section1_element.find("TITLE")
        if title_element is not None and title_element.text:
            raw_title = title_element.text.strip()
            section_data["sec_id"] = idx + 1
            section_data["sec_title"] = raw_title

        collected_items_for_section = []
        for child_of_section1 in section1_element:
            if child_of_section1.tag == "TITLE":
                continue
            extract_content_recursive(child_of_section1, collected_items_for_section)

        # 콘텐츠를 최종 문자열로 합치기
        final_sec_content_parts_builder = []

        # 이전 항목의 타입 추적 (텍스트와 테이블 사이에 줄바꿈을 넣기 위함)
        prev_type = None

        for item in collected_items_for_section:
            current_content = item["content"]
            current_type = item["type"]

            # 텍스트와 테이블 사이에만 단일 줄바꿈을 넣고 싶을 때
            if final_sec_content_parts_builder:  # 첫 항목이 아닐 경우
                if prev_type != current_type or (
                    current_type == "text" and not current_content.strip()
                ):  # 타입이 바뀌거나, 텍스트인데 공백만 있을 경우 (연속된 텍스트라도 새로운 문단처럼)
                    # 기존 마지막 항목이 이미 줄바꿈으로 끝나는지 확인하여 중복 방지
                    if not final_sec_content_parts_builder[-1].endswith("\n"):
                        final_sec_content_parts_builder.append("\n")

            final_sec_content_parts_builder.append(current_content)
            prev_type = current_type

        # 모든 부분을 합치고 최종적으로 줄바꿈과 공백을 정리
        raw_final_content = "".join(final_sec_content_parts_builder).strip()

        # 모든 연속된 공백(줄바꿈 포함)을 단일 공백으로 대체. HTML 태그 내의 공백도 영향을 받음.
        final_sec_content = re.sub(r"\s+", " ", raw_final_content)

        # 최종적으로 줄바꿈을 한 개만 남김 (이전 단계에서 이미 많이 정리되었지만 혹시 모를 상황 대비)
        final_sec_content = re.sub(r"\n+", "\n", final_sec_content)

        # 시작/끝 공백 제거
        final_sec_content = final_sec_content.strip()

        section_data["sec_content"] = final_sec_content
        report_data["sections"].append(section_data)

    return report_data

# if __name__ == "__main__":
#     # XML_FILE_PATH = "20240430000817.xml"
#     # XML_FILE_PATH = "20240516000056.xml"
#     XML_FILE_PATH = "20240514001094.xml"
#     with codecs.open(XML_FILE_PATH, "r", encoding="utf-8") as f:
#         xml_content = f.read()
#     parsed_data = parse_darter_xml(xml_content, os.path.basename(XML_FILE_PATH))
#     if parsed_data:
#         print(json.dumps(parsed_data, ensure_ascii=False, indent=2))
#     else:
#         print("Parsing failed.")