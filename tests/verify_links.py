import os
import re
from pathlib import Path

docs_dir = Path("docs")
readme = Path("README.md")

all_files = list(docs_dir.rglob("*.md")) + [readme]

broken_links = []

link_pattern = re.compile(r'\]\(([^)]+)\)')

for filepath in all_files:
    content = filepath.read_text(encoding='utf-8')
    links = link_pattern.findall(content)
    
    for link in links:
        if link.startswith('http') or link.startswith('#') or link.startswith('mailto:'):
            continue
            
        target_path = (filepath.parent / link).resolve()
        if not target_path.exists():
            broken_links.append(f"{filepath}: Broken link -> {link}")

if broken_links:
    print("Found broken links:")
    for b in broken_links:
        print(b)
else:
    print("All internal relative links are valid!")
