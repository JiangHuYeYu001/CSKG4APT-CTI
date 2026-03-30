import fitz
import sys

# 设置UTF-8输出
sys.stdout.reconfigure(encoding='utf-8')

pdf_path = 'Ren 等 - 2023 - CSKG4APT A cybersecurity knowledge graph for advanced persistent threat organization attribution.pdf'
doc = fitz.open(pdf_path)

print(f"Total pages: {len(doc)}\n")

for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()

    print(f"\n{'='*70}")
    print(f"PAGE {page_num + 1}/{len(doc)}")
    print(f"{'='*70}\n")
    print(text)

doc.close()
