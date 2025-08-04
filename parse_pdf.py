import pdfplumber
import re
from collections import OrderedDict

chapter_re = re.compile(r'^제\s*(\d+)\s*장\s*(.*)')
section_re = re.compile(r'^제\s*(\d+)\s*절\s*(.*)')
article_re = re.compile(r'^(제\s*\d+(?:-\d+)*조)(?:\(([^)]+)\))?')

def parse_pdf_to_articles(pdf_path):
    docs = []
    current = None
    chapter = section = None
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if not text:
                continue
            for line in text.split('\n'):
                s = line.strip()
                if not s:
                    continue
                m_ch = chapter_re.match(s)
                if m_ch:
                    chapter = {"num": int(m_ch.group(1)), "name": m_ch.group(2).strip()}
                    continue
                m_sec = section_re.match(s)
                if m_sec:
                    section = {"num": int(m_sec.group(1)), "name": m_sec.group(2).strip()}
                    continue
                m_art = article_re.match(s)
                if m_art:
                    if current:
                        docs.append(current)
                    raw_num = m_art.group(1)              # e.g. "제1-1-1조"
                    title = (m_art.group(2) or "").strip()
                    numbers = re.sub(r'\D', '', raw_num)  # 숫자만 → e.g. "111"
                    doc_id = numbers.zfill(6)             # e.g. "000111"
                    current = OrderedDict([
                        ("doc_id", chapter["num"]*100000 + section["num"]*1000 + int(numbers)),
                        ("chapter_num", chapter["num"]),
                        ("chapter_name", chapter["name"]),
                        ("section_num", section["num"]),
                        ("section_name", section["name"]),
                        ("article_num", re.sub(r'제|조', '', raw_num)),
                        ("article_title", title),
                        ("doc_content", "")
                    ])
                    continue
                if current:
                    current["doc_content"] += line + "\n"
    if current:
        docs.append(current)
    return docs
