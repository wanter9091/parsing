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
    # Header(TH/TE/TD)에 P 포함 가능
    headers = []
    for th in table_elem.findall('.//TH'):
        headers.append(get_cell_text(th))
    # 헤더가 없으면 첫 행에서 직접 추출 시도
    if not headers:
        first_tr = table_elem.find('.//TR')
        if first_tr is not None:
            for cell_tag in ['TH', 'TE', 'TD', 'TU']:
                for td in first_tr.findall('.//' + cell_tag):
                    headers.append(get_cell_text(td))
    rows = []
    if headers:
        rows.append(headers)
    # 모든 행 파싱
    for tr in table_elem.findall('.//TR'):
        row = []
        for cell_tag in ['TH', 'TE', 'TD', 'TU']:
            for td in tr.findall('.//' + cell_tag):
                row.append(get_cell_text(td))
        if row:
            rows.append(row)
    # 마크다운 변환
    if not rows:
        return ''
    md = '| ' + ' | '.join(rows[0]) + ' |\n'
    md += '|' + '|'.join(['---'] * len(rows[0])) + '|\n'
    for row in rows[1:]:
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
