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

def table_xml_to_json(table_elem):
    # 2차원 배열: 각 셀은 {'text': ..., 'colspan':..., 'rowspan':...}
    rows = []
    for tr in table_elem.findall('.//TR'):
        row = []
        for cell_tag in ['TH', 'TE', 'TD', 'TU']:
            for td in tr.findall(cell_tag):
                cell_text = get_cell_text(td)
                colspan = int(td.get('COLSPAN', td.get('colspan', '1')))
                rowspan = int(td.get('ROWSPAN', td.get('rowspan', '1')))
                cell_info = {'text': cell_text, 'colspan': colspan, 'rowspan': rowspan}
                row.append(cell_info)
        if row:
            rows.append(row)
    return rows

def expand_table_json(json_rows):
    # 실제 셀 배치대로 펼친 2차원 배열 생성 (병합셀은 동일값 반복)
    max_row_count = len(json_rows)
    # 우선 각 행마다 전체 칸수를 세야 함
    # 병합 해제: 각 행의 colspan/rowspan 반영
    result = []
    filled = {}
    for row_idx, row in enumerate(json_rows):
        result_row = []
        col_idx = 0
        while len(result_row) < 100:  # 테이블 100칸 넘지 않는다고 가정
            # 병합에 의해 채워져야 할 자리면 이전값 복사
            if (row_idx, col_idx) in filled:
                result_row.append(filled[(row_idx, col_idx)])
                col_idx += 1
                continue
            # 행 데이터 끝났으면 break
            if not row:
                break
            cell = row.pop(0)
            # colspan, rowspan 반영
            colspan, rowspan = cell['colspan'], cell['rowspan']
            for cs in range(colspan):
                result_row.append(cell['text'])
                # rowspan 칸은 filled에 기록(향후 행에서 복사)
                for rs in range(1, rowspan):
                    filled[(row_idx + rs, col_idx)] = cell['text']
                col_idx += 1
            if not row:
                break
        # result_row가 데이터 없는 경우 skip하지 말고, 무조건 append
        result.append(result_row)
    # 마지막으로 max_cols로 padding
    max_cols = max((len(r) for r in result), default=0)
    result = [r + [''] * (max_cols - len(r)) for r in result]
    return result

def array_to_markdown(rows):
    # 설명/단위/공백 등 분리, 나머지는 표로
    description = []
    data_rows = []
    for r in rows:
        if len(r) < 2 or all(not v for v in r):
            if any(r):
                description.append(' '.join(r))
        else:
            data_rows.append(r)
    if not data_rows:
        return ''
    # 헤더=첫 행
    header = data_rows[0]
    data = data_rows[1:]
    md = ''
    if description:
        md += '\n'.join(description) + '\n\n'
    md += '| ' + ' | '.join(header) + ' |\n'
    md += '|' + '|'.join(['---'] * len(header)) + '|\n'
    for row in data:
        md += '| ' + ' | '.join(row) + ' |\n'
    return md.strip()

def table_to_markdown(table_elem):
    json_rows = table_xml_to_json(table_elem)
    array_rows = expand_table_json(json_rows)
    return array_to_markdown(array_rows)

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
