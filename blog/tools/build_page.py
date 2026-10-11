"""중국산프리 블로그 복붙 페이지 생성기
사용: python3 -I build_page.py <repo_dir> <body.html> <title.txt> <tags.txt> <out.html> "<페이지 이름, 예: 블로그 #392 고춧가루>"
- body.html 안의 이미지는 <img data-repo="DB_img/Source/raw_xxx.jpg" ...> 형태로 레포 경로만 적는다
- 미리보기용으로 이미지를 페이지에 박아 넣고, "본문 복사" 시에는 jsDelivr 주소로 바꿔서 복사되게 한다
  (네이버 에디터는 data: 이미지를 거부하고 웹 주소 이미지만 받음)
"""
import base64, io, os, re, sys
from PIL import Image

repo, body_p, title_p, tags_p, out, page_title = sys.argv[1:7]
CDN = "https://cdn.jsdelivr.net/gh/joongfree/data@main"
here = os.path.dirname(os.path.abspath(__file__))

def data_uri(path):
    im = Image.open(path)
    buf = io.BytesIO()
    if path.lower().endswith(".png") and im.mode in ("RGBA", "LA", "P"):
        im.save(buf, "PNG", optimize=True); mime = "image/png"
    else:
        im.convert("RGB").save(buf, "JPEG", quality=88, optimize=True); mime = "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode()

def swap(m):
    rel = m.group(1)
    local = os.path.join(repo, rel)
    if not os.path.exists(local):
        sys.exit(f"이미지 없음: {rel}")
    return f'<img data-cdn="{CDN}/{rel}" src="{data_uri(local)}"'

body = open(body_p, encoding="utf-8").read()
body = re.sub(r'<img data-repo="([^"]+)"', swap, body)
title = open(title_p, encoding="utf-8").read().strip()
tags = open(tags_p, encoding="utf-8").read().strip()
tpl = open(os.path.join(here, "copy_page.html"), encoding="utf-8").read()
html = tpl.replace("{{PAGE_TITLE}}", page_title).replace("{{TITLE}}", title).replace("{{TAGS}}", tags).replace("{{POST}}", body)
open(out, "w", encoding="utf-8").write(html)
print(out, len(html))
