import re

# 1. 모든 `<`와 `>`를 우선 엔티티로 변환
encoded_xml = xml_string.replace("<", "&lt;").replace(">", "&gt;")

# 2. 화이트리스트 태그만 원래대로 복원
WHITELIST = {
        "DOCUMENT", "DOCUMENT-NAME", "FORMULA-VERSION", "COMPANY-NAME", "SUMMARY",
        "LIBRARY", "BODY", "EXTRACTION", "COVER", "COVER-TITLE",
        "IMAGE", "IMG", "IMG-CAPTION", "P", "A", "SPAN",
        "TR", "TD", "TH", "TE", "TU", "SECTION-1", "SECTION-2", "SECTION-3",
        "TITLE", "TABLE", "TABLE-GROUP", "COLGROUP", "COL", "THEAD",
        "TBODY", "PGBRK", "PART",
    }

# 태그 이름만 추출하는 정규식: &lt;/TD&gt; -> /TD, &lt;TD ...&gt; -> TD ...
TAG_RE = re.compile(r"&lt;(/?)(\w+)([^&]*)&gt;")

def restore_whitelisted_tags(match):
    slash, tag, attrs = match.groups()
    if tag.upper() in WHITELIST:
        return f"<{slash}{tag}{attrs}>"
    return match.group(0) # 화이트리스트에 없으면 그대로 둠

cleaned_xml = TAG_RE.sub(restore_whitelisted_tags, encoded_xml)

# 이제 cleaned_xml을 XML 파서로 처리