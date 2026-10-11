"""중국산프리 블로그 썸네일 생성기
사용: python3 -I thumb.py <template.png> <product_image> <out.jpg> "<1줄 문구>" "<2줄 강조어>" "<2줄 나머지>"
예:   python3 -I thumb.py blog/thumb_template.png pr.png out.jpg "중국산 원료 없는" "고춧가루" " 소개"
- 1068x600 가로형이지만, 가운데 600x600 정사각형으로 잘려 보여도 제품과 문구가 안 벗어나게 배치함
- 흰 배경 제품 사진은 누끼를 따고, 배경이 흰색이 아니면 흰 카드에 넣어서 배치함
"""
import sys
from collections import deque
from PIL import Image, ImageDraw, ImageFont, ImageFilter

tpl_path, prod_path, out, line1, hi, rest = sys.argv[1:7]
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
WHITE, YELLOW = (255, 255, 255, 255), (255, 226, 52, 255)

bg = Image.open(tpl_path).convert("RGBA")
W, H = bg.size
SAFE = min(W, H) - 80          # 정사각형(600) 안쪽 여백 40px씩 → 520px
TEXT_MAX = SAFE
PROD_MAX_W, PROD_MAX_H = 360, 255

def cutout(img):
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    white = lambda c: c[0] > 238 and c[1] > 238 and c[2] > 238
    mask = Image.new("L", (w, h), 255); m = mask.load()
    seen = bytearray(w * h); q = deque()
    for x in range(w): q.extend([(x, 0), (x, h - 1)])
    for y in range(h): q.extend([(0, y), (w - 1, y)])
    removed = 0
    while q:
        x, y = q.popleft(); i = y * w + x
        if seen[i]: continue
        seen[i] = 1
        if not white(px[x, y]): continue
        m[x, y] = 0; removed += 1
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                q.append((nx, ny))
    if removed < w * h * 0.05:      # 흰 배경이 아님 → 흰 카드로
        return None
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    img.putalpha(mask)
    return img.crop(img.getbbox())

def card(img):
    img = img.convert("RGB")
    img.thumbnail((PROD_MAX_W - 24, PROD_MAX_H - 24), Image.LANCZOS)
    c = Image.new("RGBA", (img.width + 24, img.height + 24), (0, 0, 0, 0))
    r = Image.new("L", c.size, 0)
    ImageDraw.Draw(r).rounded_rectangle([0, 0, c.width - 1, c.height - 1], 18, fill=255)
    c.paste(Image.new("RGBA", c.size, (255, 255, 255, 255)), (0, 0), r)
    c.paste(img, (12, 12))
    return c

src = Image.open(prod_path)
p = cutout(src) or card(src)
scale = min(PROD_MAX_W / p.width, PROD_MAX_H / p.height)
p = p.resize((round(p.width * scale), round(p.height * scale)), Image.LANCZOS)
x0 = (W - p.width) // 2
y0 = 172 + (PROD_MAX_H - p.height) // 2

sh = Image.new("RGBA", bg.size, (0, 0, 0, 0))
shadow = Image.new("RGBA", p.size, (10, 40, 90, 255))
shadow.putalpha(p.split()[3].point(lambda v: int(v * 0.35)))
sh.paste(shadow, (x0 + 6, y0 + 10), shadow)
bg = Image.alpha_composite(bg, sh.filter(ImageFilter.GaussianBlur(10)))
bg.alpha_composite(p, (x0, y0))

# 두 줄 중 긴 쪽이 520px 안에 들어오도록 글자 크기 자동 조절
size = 58
while True:
    font = ImageFont.truetype(FONT, size, index=1)
    d = ImageDraw.Draw(bg)
    widest = max(d.textlength(line1, font=font), d.textlength(hi + rest, font=font))
    if widest <= TEXT_MAX or size <= 36: break
    size -= 2

def draw_line(img, y, parts):
    d = ImageDraw.Draw(img)
    total = sum(d.textlength(t, font=font) for t, _ in parts)
    x = (W - total) / 2
    sl = Image.new("RGBA", img.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sl); xx = x
    for t, _ in parts:
        sd.text((xx + 2, y + 4), t, font=font, fill=(0, 30, 80, 150)); xx += d.textlength(t, font=font)
    img = Image.alpha_composite(img, sl.filter(ImageFilter.GaussianBlur(4)))
    d = ImageDraw.Draw(img)
    for t, c in parts:
        d.text((x, y), t, font=font, fill=c); x += d.textlength(t, font=font)
    return img

gap = size + 12
bg = draw_line(bg, 438 + (58 - size) // 2, [(line1, WHITE)])
bg = draw_line(bg, 438 + gap + (58 - size) // 2, [(hi, YELLOW), (rest, WHITE)])
bg.convert("RGB").save(out, quality=92)
print(out, bg.size, "font", size)
