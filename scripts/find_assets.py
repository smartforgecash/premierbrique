import re
from pathlib import Path

html_files = list(Path('.').glob('**/*.html'))
urls = set()

for file in html_files:
    if '.venv' in file.parts or 'node_modules' in file.parts:
        continue
    try:
        content = file.read_text(encoding='utf-8')
        # match urls like https://cdn.prod.website-files.com/... or similar
        found = re.findall(r'(https://cdn\.prod\.website-files\.com/[^\s"\'\)>]+)', content)
        for url in found:
            # clean up query parameters or trailing punctuation
            url_clean = url.split('?')[0].split(')')[0].split('"')[0].split("'")[0]
            urls.add(url_clean)
    except Exception as e:
        print(f"Error reading {file}: {e}")

print(f"Found {len(urls)} unique Webflow assets:")
# filter for images (png, webp, jpg, jpeg)
images = [url for url in urls if url.lower().endswith(('.png', '.webp', '.jpg', '.jpeg'))]
print(f"Found {len(images)} unique images:")
for img in sorted(images):
    print(img)
