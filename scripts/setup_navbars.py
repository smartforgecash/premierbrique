import re
from pathlib import Path

workspace = Path(__file__).resolve().parent.parent

# 1. Update index.html
index_path = workspace / "index.html"
if index_path.exists():
    content = index_path.read_text(encoding="utf-8")
    
    # We find the navbar block by matching the transparent navbar div up to the navbar_script div
    navbar_regex = re.compile(
        r'<div data-animation="default" class="navbar w-nav"[^>]*id="navbar">.*?</div></div></div>(?=<div class="navbar_script)',
        re.DOTALL
    )
    
    new_content, count = navbar_regex.subn(
        '{% include "navbar.html" with navbar_variant="transparent" %}',
        content
    )
    if count > 0:
        index_path.write_text(new_content, encoding="utf-8")
        print("Updated index.html navbar")
    else:
        print("Error: Could not find navbar in index.html")

# 2. Update base_app.html
base_app_path = workspace / "investments" / "templates" / "investments" / "base_app.html"
if base_app_path.exists():
    content = base_app_path.read_text(encoding="utf-8")
    
    navbar_regex = re.compile(
        r'<div data-animation="default" class="navbar w-nav"[^>]*id="navbar">.*?</div>\s+</div>\s+</div>(?=\s+<!-- Main Page Content -->)',
        re.DOTALL
    )
    
    new_content, count = navbar_regex.subn(
        '{% include "navbar.html" with navbar_variant="white" %}',
        content
    )
    if count > 0:
        base_app_path.write_text(new_content, encoding="utf-8")
        print("Updated base_app.html navbar")
    else:
        print("Error: Could not find navbar in base_app.html")

# 3. Update public-page.html
public_page_path = workspace / "public-page.html"
if public_page_path.exists():
    content = public_page_path.read_text(encoding="utf-8")
    new_content, count = re.subn(
        r'<div id="navbar"></div>',
        '{% include "navbar.html" with navbar_variant="white" %}',
        content
    )
    if count > 0:
        public_page_path.write_text(new_content, encoding="utf-8")
        print("Updated public-page.html navbar")
    else:
        print("Error: Could not find navbar in public-page.html")
