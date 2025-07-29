import re
from lxml import etree

def preprocess_xml(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        xml_str = f.read()
    # 태그로 오인될 수 있는 한글 <xxx> 패턴 치환
    xml_str = re.sub(r'<([가-힣]{2,10})>', r'&lt;\1&gt;', xml_str)
    return xml_str

def get_cell_text(cell):
    # 셀 내 모든 하위 text 추출 (공백, 특수문자도 정리)
    text = ''.join(cell.itertext())
    text = text.replace('\xa0', ' ').replace('　', '').strip()
    return text

def table_to_markdown(table_elem):
    # 모든 행(row)을 무조건 2차원 배열로 수집 (설명, 헤더, 데이터 모두)
    all_rows = []
    for tr in table_elem.findall('.//TR'):
        row = []
        for cell_tag in ['TH', 'TE', 'TD', 'TU']:
            for td in tr.findall('.//' + cell_tag):
                cell_text = get_cell_text(td)
                row.append(cell_text)
        all_rows.append(row)
    
    # 컬럼수: 실제 데이터가 가장 많이 들어있는 행의 길이로 결정
    max_cols = max((len(r) for r in all_rows if len(r) > 1), default=0)

    # 데이터 행: 컬럼이 3개 이상인 행만 데이터/헤더 후보로 간주
    data_candidate_rows = [r for r in all_rows if len(r) >= 3]
    if not data_candidate_rows:
        return ''  # 데이터 없는 빈 테이블 예외 처리

    # 헤더: 마지막 컬럼이 3개 이상인 행을 컬럼명으로 (보통 회계표 마지막 헤더행)
    header_row = data_candidate_rows[0]
    data_rows = data_candidate_rows[1:]

    # 혹시 데이터가 1행만 있으면 header/data 재정의
    if len(data_rows) == 0 and len(data_candidate_rows) > 1:
        header_row = data_candidate_rows[-2]
        data_rows = [data_candidate_rows[-1]]
    elif len(data_rows) == 0:
        # (실데이터가 한줄 뿐인 테이블, 예외적으로 처리)
        data_rows = []

    # 설명/단위/공백 등은 모두 그 앞쪽(all_rows에서 컬럼이 3개 미만인 행)에서 추출
    description_lines = [' '.join(r) for r in all_rows if len(r) < 3 and any(r)]

    # 각 행을 max_cols 기준으로 패딩
    def pad(row): return row + [''] * (max_cols - len(row))
    header_row = pad(header_row)
    data_rows = [pad(r) for r in data_rows]

    # 마크다운 표 생성
    md = ''
    if description_lines:
        md += '\n'.join(description_lines) + '\n\n'
    md += '| ' + ' | '.join(header_row) + ' |\n'
    md += '|' + '|'.join(['---'] * len(header_row)) + '|\n'
    for row in data_rows:
        md += '| ' + ' | '.join(row) + ' |\n'
    return md.strip()


def replace_tables_with_markdown(xml_str):
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml_str.encode('utf-8'), parser=parser)
    for table in root.findall('.//TABLE'):
        md_table = table_to_markdown(table)
        # TABLE 태그 위치에 마크다운 표 삽입
        parent = table.getparent()
        if parent is not None:
            md_elem = etree.Element('P')
            md_elem.text = '\n' + md_table + '\n'
            parent.replace(table, md_elem)
    return etree.tostring(root, encoding='unicode')

def clean_whitespace(text):
    # 연속 개행 줄이기
    text = re.sub(r'\n+', '\n', text)
    # 각 줄 앞뒤 공백 제거
    text = '\n'.join(line.strip() for line in text.splitlines())
    # 연속되는 공백은 1칸으로
    text = re.sub(r' +', ' ', text)
    # 연속되는 개행 2번 이하로 줄이기
    text = re.sub(r'\n{2,}', '\n\n', text)
    return text.strip()

def parse_and_extract_sections(xml_str):
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml_str.encode('utf-8'), parser=parser)
    sections = {}
    for section in root.xpath('.//SECTION-1'):
        title_elem = section.find('TITLE')
        title = title_elem.text if title_elem is not None else ''
        section_num = ''
        match = re.match(r'([IVXLCDM]+)\.', title)
        if match:
            section_num = match.group(1)
        content = etree.tostring(section, encoding='unicode', method='text')
        content = clean_whitespace(content)
        sections[section_num] = {
            'title': title,
            'content': content
        }
    return sections

def main():
    file_path = '20240430000817.xml'
    xml_str = preprocess_xml(file_path)
    xml_with_md = replace_tables_with_markdown(xml_str)
    sections = parse_and_extract_sections(xml_with_md)
    # 결과 출력 및 저장
    print(sections)
    with open('output.txt', 'w', encoding='utf-8') as f:
        for section_num, section in sections.items():
            f.write(f"Section {section_num}:\n")
            f.write(f"Title: {section['title']}\n")
            f.write(f"Content:\n{section['content']}\n\n")

if __name__ == "__main__":
    main()
