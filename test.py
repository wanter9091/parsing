xml_file = '20240430000817.xml'

with open(xml_file, encoding='utf-8') as f:
    for i, line in enumerate(f, start=1):
        if 5600 <= i <= 5610:
            print(f"{i:>5}: {line.rstrip()}")