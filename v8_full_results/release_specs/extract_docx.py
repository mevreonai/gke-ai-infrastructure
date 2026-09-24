import zipfile
import xml.etree.ElementTree as ET

def extract_docx_text(docx_path):
    with zipfile.ZipFile(docx_path, 'r') as docx:
        doc_xml = docx.read('word/document.xml')
        root = ET.fromstring(doc_xml)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        paragraphs = []
        for p in root.findall('.//w:p', ns):
            p_text = []
            for r in p.findall('.//w:t', ns):
                if r.text:
                    p_text.append(r.text)
            paragraphs.append(''.join(p_text))
        return '\n'.join(paragraphs)

text = extract_docx_text('release_specs/V8_Dashboard_realrun_v4_new_latest_RAW_DATA_DEEP_AUDIT_AIPromptMessage.docx')
with open('release_specs/docx_text.txt', 'w', encoding='utf-8') as f:
    f.write(text)
print("Successfully extracted DOCX text. Total characters:", len(text))
