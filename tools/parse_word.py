import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

docs = list(Path('docs').glob('*.docx'))
print('Found docs:', docs)
for d in docs:
    with zipfile.ZipFile(d) as z:
        xml = z.read('word/document.xml')
        root = ET.fromstring(xml)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        texts = [t.text for t in root.iter(f'{{{ns["w"]}}}t') if t.text]
        out_path = Path('docs/test_doc_' + str(d.stat().st_size) + '.txt')
        out_path.write_text('\n'.join(texts[:100]), encoding='utf-8')
        print('Wrote', out_path)
