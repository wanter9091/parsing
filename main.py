import re
from lxml import etree

def preprocess_xml(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        xml_str = f.read()
    xml_str = re.sub(r'<([가-힣]{2,10})>', r'&lt;\1&gt;', xml_str)
    return xml_str

def get_cell_text(cell):
    text = ''.join(cell.itertext())
    text = text.replace('\xa0', ' ').replace('　', '').strip()
    return text

def table_xml_to_structured_json(table_elem):
    # 2차원 구조 + 각 셀에 text, colspan, rowspan
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
    # 병합셀까지 반영, 마크다운 표로 뽑을 수 있게 2차원 배열로 확장
    result = []
    filled = {}  # (row_idx, col_idx) : value
    for row_idx, row in enumerate(json_rows):
        result_row = []
        col_idx = 0
        while col_idx < 100:  # max column 수 가정
            # 병합 복사
            if (row_idx, col_idx) in filled:
                result_row.append(filled[(row_idx, col_idx)])
                col_idx += 1
                continue
            if not row:
                break
            cell = row.pop(0)
            text = cell['text']
            colspan, rowspan = cell['colspan'], cell['rowspan']
            for cs in range(colspan):
                result_row.append(text if cs == 0 else '')
                # rowspan 복사 세팅
                for rs in range(1, rowspan):
                    filled[(row_idx + rs, col_idx)] = '' if cs > 0 else text
                col_idx += 1
        result.append(result_row)
    # 컬럼수 정렬
    max_cols = max((len(r) for r in result), default=0)
    result = [r + [''] * (max_cols - len(r)) for r in result]
    return result

def markdown_from_2d(rows):
    # description(설명/단위)와 표 구분
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
    # 멀티헤더 감지: 연속적으로 문자열 포함된 행이 여러 개면 헤더로 모두 사용
    header_lines = []
    data_start = 0
    for i, row in enumerate(data_rows):
        # 데이터가 완전히 숫자/공란이거나, 첫 줄이 아닌데 1~2글자 이하면 데이터
        if i == 0 or (any(len(cell) > 1 for cell in row)):
            header_lines.append(row)
        else:
            data_start = i
            break
    else:
        data_start = len(header_lines)
    # 최소 1줄 헤더 보장
    if not header_lines:
        header_lines.append(data_rows[0])
        data_start = 1
    # 마크다운 생성
    md = ''
    if description:
        md += '\n'.join(description) + '\n\n'
    for i, h in enumerate(header_lines):
        md += '| ' + ' | '.join(h) + ' |\n'
        if i == len(header_lines) - 1:
            md += '|' + '|'.join(['---'] * len(h)) + '|\n'
    for row in data_rows[data_start:]:
        md += '| ' + ' | '.join(row) + ' |\n'
    return md.strip()

def table_to_markdown(table_elem):
    # 전체 파이프라인: XML→JSON→2D array→마크다운
    json_rows = table_xml_to_structured_json(table_elem)
    expanded = expand_table_json(json_rows)
    return markdown_from_2d(expanded)

def replace_tables_with_markdown(xml_str):
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml_str.encode('utf-8'), parser=parser)
    for table in root.findall('.//TABLE'):
        md_table = table_to_markdown(table)
        parent = table.getparent()
        if parent is not None:
            md_elem = etree.Element('P')
            md_elem.text = '\n' + md_table + '\n'
            parent.replace(table, md_elem)
    return etree.tostring(root, encoding='unicode')

def clean_whitespace(text):
    text = re.sub(r'\n+', '\n', text)
    text = '\n'.join(line.strip() for line in text.splitlines())
    text = re.sub(r' +', ' ', text)
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
    print(sections)
    with open('output.txt', 'w', encoding='utf-8') as f:
        for section_num, section in sections.items():
            f.write(f"Section {section_num}:\n")
            f.write(f"Title: {section['title']}\n")
            f.write(f"Content:\n{section['content']}\n\n")

if __name__ == "__main__":
    main()
