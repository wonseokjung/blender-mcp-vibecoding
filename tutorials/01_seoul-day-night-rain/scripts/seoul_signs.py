# Seoul street signage textures (generic made-up shop names, no real brands). PNG RGB; emission uses the same image.
from PIL import Image, ImageDraw, ImageFont
D = "assets/signs/"
F = lambda w, s: ImageFont.truetype(f"fonts/Pretendard-{w}.otf", s)
def sign(name, w, h, bg, lines, fg=(255, 255, 255), weight="ExtraBold", vertical=False, border=None, sub=None):
    im = Image.new("RGB", (w, h), bg); d = ImageDraw.Draw(im)
    if border: d.rectangle([6, 6, w - 7, h - 7], outline=border, width=8)
    if vertical:
        chars = list(lines); n = len(chars); cs = min(int(w*0.72), int(h*0.86/n))
        for i, ch in enumerate(chars):
            d.text((w/2, h*0.07 + cs*0.5 + i*(h*0.86/n)), ch, font=F(weight, cs), fill=fg, anchor="mm")
    else:
        size = int(h*0.62) if not sub else int(h*0.5)
        f = F(weight, size)
        while d.textlength(lines, font=f) > w*0.9: size -= 4; f = F(weight, size)
        d.text((w/2, h*(0.5 if not sub else 0.42)), lines, font=f, fill=fg, anchor="mm")
        if sub: d.text((w/2, h*0.82), sub, font=F("SemiBold", int(h*0.16)), fill=fg, anchor="mm")
    im.save(D + name + ".png")
# hero: CONNECT AI LAB shop fascia (black, white light type + Matrix-green cursor)
im = Image.new("RGB", (3000, 420), (8, 9, 10)); d = ImageDraw.Draw(im)
f = F("Light", 200); x = 230; tr = 34
for ch in "CONNECT AI LAB":
    d.text((x, 210), ch, font=f, fill=(242, 242, 238), anchor="lm"); x += d.textlength(ch, font=f) + tr
d.rectangle([x + 10, 110, x + 52, 310], fill=(0, 255, 65))
im.save(D + "cal_fascia.png")
sign("v_cafe", 300, 1500, (20, 24, 28), "카페온도", fg=(255, 214, 140), weight="Bold", vertical=True, border=(255, 214, 140))
sign("v_piano", 280, 1400, (250, 250, 248), "피아노학원", fg=(30, 60, 160), weight="ExtraBold", vertical=True)
sign("v_dental", 280, 1200, (16, 120, 110), "미소치과", fg=(255, 255, 255), vertical=True)
sign("v_karaoke", 300, 1500, (120, 20, 120), "노래연습장", fg=(255, 230, 255), vertical=True)
sign("v_pc", 280, 1000, (10, 30, 90), "PC방", fg=(120, 220, 255), vertical=True)
sign("h_bunsik", 2200, 420, (200, 30, 30), "서울분식", fg=(255, 245, 220), sub="김밥 · 떡볶이 · 라면")
sign("h_mart", 2200, 420, (20, 70, 170), "24시 동네마트", fg=(255, 255, 255))
sign("h_laundry", 1800, 400, (245, 245, 240), "크린세탁", fg=(20, 90, 180))
sign("h_pharm", 1600, 400, (20, 140, 70), "온누리약국", fg=(255, 255, 255))
sign("h_flower", 1800, 400, (250, 236, 230), "꽃집 봄날", fg=(180, 40, 80), weight="Bold")
sign("h_chicken", 2000, 420, (240, 170, 20), "바삭치킨", fg=(70, 30, 10))
sign("h_realty", 1800, 400, (30, 30, 34), "행복공인중개사", fg=(255, 220, 120), weight="Bold")
sign("w_academy", 1600, 300, (255, 255, 255), "수학 · 영어 학원", fg=(220, 30, 40))
print("signs ok")
