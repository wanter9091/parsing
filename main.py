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
    # 설명행/단위행/헤더행 분리
    description_lines = []
    data_rows = []
    headers = []
    found_header = False

    for tr in table_elem.findall('.//TR'):
        row = []
        for cell_tag in ['TH', 'TE', 'TD', 'TU']:
            for td in tr.findall('.//' + cell_tag):
                cell_text = get_cell_text(td)
                row.append(cell_text)
        # 설명/단위/공백 등은 description으로 저장
        if not found_header and (len(row) == 1 or all(not c for c in row)):
            if any(row):
                description_lines.append(' '.join(row))
            continue
        # 첫 헤더(컬럼명이 여러개 이상이면 헤더로 간주)
        if not found_header and len(row) > 1:
            headers = row
            found_header = True
            continue
        # 데이터 행
        if found_header and row:
            data_rows.append(row)

    # 마크다운 표 생성
    md = ''
    if description_lines:
        md += '\n'.join(description_lines) + '\n\n'
    if headers:
        md += '| ' + ' | '.join(headers) + ' |\n'
        md += '|' + '|'.join(['---'] * len(headers)) + '|\n'
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
