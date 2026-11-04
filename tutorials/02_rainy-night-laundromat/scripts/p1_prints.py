"""Printed graphics for #1 (signs/stickers are textures, never 3D text): sign face, notice poster, machine stickers,
door vinyl, floor sticker. Each print gets fade / yellowing / grime so it reads as a real aged print."""
import os, random, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance
import numpy as np
O = os.path.expanduser('tex1'); os.makedirs(O, exist_ok=True)
F = lambda w, s: ImageFont.truetype(os.path.expanduser('~/Library/Fonts/Pretendard-%s.otf' % w), s)
rng = np.random.default_rng(3)


def age(img, yellow=0.10, fade=0.08, grime=0.12, seed=0):
    r = np.random.default_rng(seed)
    a = np.asarray(img.convert('RGB')).astype(np.float32) / 255
    h, w = a.shape[:2]
    # low-freq blotches
    n = r.random((max(2, h // 64), max(2, w // 64)))
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
    a = a * (1 - fade) + fade * 0.85                     # fade toward paper
    a = a * np.array([1.0, 1.0 - yellow * 0.4, 1.0 - yellow])  # yellowing
    a = a * (1 - grime * n[..., None] * 0.8)
    # vertical drip streaks from the top edge
    for _ in range(int(w / 60)):
        x = r.integers(0, w); L = r.integers(h // 6, h // 2); wd = r.integers(2, 6)
        a[:L, max(0, x - wd):x + wd] *= (1 - grime * 0.5 * np.linspace(1, 0, L))[:, None, None]
    # fine speckle
    a *= 1 - grime * 0.25 * r.random((h, w, 1))
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))


# 1) light-box sign face (white acrylic, blue + coral print), 2400 x 420  (5.4 m x 0.65 m)
W, H = 2400, 420
im = Image.new('RGB', (W, H), (246, 246, 242)); d = ImageDraw.Draw(im)
BLUE = (18, 72, 160); CORAL = (226, 64, 54); NAVY = (14, 34, 78)
d.rectangle([0, H - 46, W, H], fill=BLUE)
d.text((W / 2, H - 23), '24시간 무인 셀프빨래방  ·  세탁 · 건조 · 운동화', font=F('Bold', 30), fill=(240, 244, 250), anchor='mm')
# washer icon
cx, cy, R = 250, 182, 118
d.rounded_rectangle([cx - R, cy - R - 20, cx + R, cy + R + 10], 26, outline=BLUE, width=14)
d.ellipse([cx - 72, cy - 58, cx + 72, cy + 86], outline=BLUE, width=14)
d.arc([cx - 40, cy - 22, cx + 40, cy + 50], 200, 340, fill=CORAL, width=10)
d.ellipse([cx + 60, cy - R + 2, cx + 82, cy - R + 24], fill=CORAL)
tx = 430
d.text((tx, 60), 'CONNECT AI LAB', font=F('ExtraBold', 150), fill=NAVY)
bb = d.textbbox((tx, 60), 'CONNECT AI LAB', font=F('ExtraBold', 150))
d.rounded_rectangle([bb[2] + 40, 82, bb[2] + 330, 222], 18, fill=CORAL)
d.text((bb[2] + 185, 152), '24H', font=F('Black', 112), fill=(255, 255, 255), anchor='mm')
d.text((tx + 6, 252), '코인 셀프빨래방', font=F('Bold', 76), fill=BLUE)
d.text((tx + 620, 268), 'SELF LAUNDRY · OPEN 24 HOURS', font=F('SemiBold', 44), fill=(120, 130, 150))
age(im, yellow=0.04, fade=0.02, grime=0.05, seed=1).save(os.path.join(O, 'sign_face.png'))

# 2) notice poster A2 portrait 1200 x 1700
W, H = 1200, 1700
im = Image.new('RGB', (W, H), (250, 249, 244)); d = ImageDraw.Draw(im)
d.rectangle([0, 0, W, 230], fill=BLUE)
d.text((W / 2, 80), '셀프빨래방 이용안내', font=F('ExtraBold', 92), fill='white', anchor='mm')
d.text((W / 2, 175), 'CONNECT AI LAB 24H', font=F('Bold', 46), fill=(200, 216, 245), anchor='mm')
steps = ['세탁물을 넣고 문을 꼭 닫아 주세요', '코스를 고르고 결제해 주세요 (카드 · 현금)', '세제는 자동 투입됩니다', '완료 후 세탁물을 바로 꺼내 주세요', '운동화는 전용 세탁기를 이용해 주세요']
y = 300
for i, t in enumerate(steps):
    d.ellipse([70, y, 150, y + 80], fill=CORAL); d.text((110, y + 40), str(i + 1), font=F('Black', 52), fill='white', anchor='mm')
    d.text((185, y + 40), t, font=F('SemiBold', 50), fill=(30, 34, 44), anchor='lm'); y += 130
y += 30
d.rectangle([70, y, W - 70, y + 6], fill=BLUE); y += 50
for name, price in (('세탁 (40분)', '4,000원'), ('건조 (30분)', '3,000원'), ('운동화 세탁', '3,000원'), ('추가 건조 10분', '1,000원')):
    d.text((90, y), name, font=F('Bold', 58), fill=(30, 34, 44)); d.text((W - 90, y), price, font=F('ExtraBold', 62), fill=BLUE, anchor='ra'); y += 100
d.rectangle([70, H - 220, W - 70, H - 80], outline=CORAL, width=6)
d.text((W / 2, H - 150), '분실물은 책임지지 않습니다  ·  CCTV 녹화중', font=F('Bold', 44), fill=CORAL, anchor='mm')
age(im, yellow=0.08, fade=0.04, grime=0.08, seed=2).save(os.path.join(O, 'poster.png'))

# 3) machine price stickers 600 x 300 (washer / dryer)
for name, line1, line2, col in (('sticker_wash', '세탁', '4,000원', BLUE), ('sticker_dry', '건조', '3,000원 / 30분', CORAL)):
    im = Image.new('RGB', (600, 300), (252, 252, 250)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 600, 96], fill=col); d.text((300, 50), line1, font=F('ExtraBold', 70), fill='white', anchor='mm')
    d.text((300, 190), line2, font=F('ExtraBold', 74 if len(line2) < 8 else 58), fill=(26, 30, 40), anchor='mm')
    d.text((300, 268), 'CONNECT AI LAB', font=F('SemiBold', 28), fill=(130, 136, 150), anchor='mm')
    age(im, yellow=0.07, fade=0.04, grime=0.10, seed=len(name)).save(os.path.join(O, name + '.png'))

# 4) door vinyl (white cut vinyl on transparent) 1600 x 900 RGBA
im = Image.new('RGBA', (1600, 900), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.text((800, 260), 'CONNECT AI LAB', font=F('Bold', 130), fill=(255, 255, 255, 255), anchor='mm')
d.text((800, 420), '24H SELF LAUNDRY', font=F('Medium', 84), fill=(255, 255, 255, 235), anchor='mm')
d.line([300, 520, 1300, 520], fill=(255, 255, 255, 200), width=5)
d.text((800, 600), '연중무휴 · 무인운영 · CCTV', font=F('SemiBold', 62), fill=(255, 255, 255, 220), anchor='mm')
a = np.asarray(im).copy(); m = rng.random(a.shape[:2]) < 0.035; a[m, 3] = (a[m, 3] * 0.3).astype(np.uint8)  # pin-hole wear
Image.fromarray(a).save(os.path.join(O, 'door_vinyl.png'))

# 5) floor caution sticker 800 x 800
im = Image.new('RGB', (800, 800), (250, 206, 40)); d = ImageDraw.Draw(im)
d.rectangle([30, 30, 770, 770], outline=(20, 20, 20), width=24)
d.text((400, 330), '미끄럼', font=F('Black', 190), fill=(20, 20, 20), anchor='mm')
d.text((400, 540), '주의', font=F('Black', 190), fill=(20, 20, 20), anchor='mm')
age(im, yellow=0.05, fade=0.10, grime=0.45, seed=9).save(os.path.join(O, 'floor_sticker.png'))

# 6) small door hanger "OPEN 24H" 600 x 260
im = Image.new('RGB', (600, 260), (22, 26, 34)); d = ImageDraw.Draw(im)
d.text((300, 110), 'OPEN', font=F('Black', 120), fill=(255, 214, 90), anchor='mm')
d.text((300, 210), '24 HOURS', font=F('Bold', 52), fill=(235, 235, 235), anchor='mm')
age(im, yellow=0.04, fade=0.04, grime=0.2, seed=11).save(os.path.join(O, 'hanger.png'))
print('prints ok', sorted(os.listdir(O)))
