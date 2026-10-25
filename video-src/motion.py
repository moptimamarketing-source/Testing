"""Minda Optima referral tutorial - 3D phone motion-design video (1080x1920, 30fps)."""
import math
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
NAVY = (11, 42, 91)
GOLD = (255, 193, 7)
WHITE = (255, 255, 255)
SOFT = (205, 212, 235)
GREY = (110, 120, 140)
LINE = (215, 222, 232)
DARK = (30, 40, 60)

_fonts = {}


def F(size, w="Regular"):
    key = (size, w)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", size)
    return _fonts[key]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, a, b):
    return clamp((t - a) / (b - a))


def ease(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def eout(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def wrap(text, fnt, maxw):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    lines, line = [], ""
    for wd in text.split():
        t = (line + " " + wd).strip()
        if d.textlength(t, font=fnt) > maxw and line:
            lines.append(line)
            line = wd
        else:
            line = t
    if line:
        lines.append(line)
    return lines


# ---------------------------------------------------------------- static assets (built once per process)
_cache = {}


def asset(name, fn):
    if name not in _cache:
        _cache[name] = fn()
    return _cache[name]


def make_bg():
    bw, bh = 1400, 2300
    sw, sh = bw // 4, bh // 4
    small = Image.new("RGB", (sw, sh))
    d = ImageDraw.Draw(small)
    top, bot = (5, 9, 30), (22, 10, 56)
    for y in range(sh):
        t = y / (sh - 1)
        d.line([(0, y), (sw, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    glow = Image.new("RGB", (sw, sh))
    g = ImageDraw.Draw(glow)
    for x, y, r, c in [(70, 140, 120, (95, 50, 210)), (300, 420, 160, (30, 70, 200)),
                       (270, 70, 70, (120, 90, 15)), (50, 500, 100, (120, 40, 180))]:
        g.ellipse([x - r, y - r, x + r, y + r], fill=c)
    glow = glow.filter(ImageFilter.GaussianBlur(55))
    arr = np.clip(np.asarray(small, np.int16) + np.asarray(glow, np.int16), 0, 255).astype(np.uint8)
    return Image.fromarray(arr).resize((bw, bh), Image.BICUBIC)


def make_vignette():
    a = np.zeros((H, W), np.float32)
    ys = np.arange(H, dtype=np.float32)
    top = np.clip(1 - ys / 640, 0, 1) ** 1.4 * 215
    bot = np.clip((ys - 1640) / 280, 0, 1) * 225
    a += np.maximum(top, bot)[:, None]
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = 5, 8, 26
    rgba[..., 3] = a.astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def background(t):
    bg = asset("bg", make_bg)
    ox = int(160 + 90 * math.sin(t * 0.35))
    oy = int(190 + 150 * math.sin(t * 0.22 + 1))
    return bg.crop((ox, oy, ox + W, oy + H)).convert("RGBA")


# ---------------------------------------------------------------- phone
SW, SH, BZ = 600, 1240, 24
PW, PH = SW + 2 * BZ, SH + 2 * BZ
SB = 54  # status bar height


def make_body():
    im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, PW - 1, PH - 1], radius=86, fill=(150, 156, 178, 255))
    d.rounded_rectangle([4, 4, PW - 5, PH - 5], radius=82, fill=(52, 56, 74, 255))
    d.rounded_rectangle([10, 10, PW - 11, PH - 11], radius=78, fill=(10, 11, 18, 255))
    return im


def make_mask():
    m = Image.new("L", (SW, SH), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, SW - 1, SH - 1], radius=62, fill=255)
    return m


def make_sheen():
    ys, xs = np.mgrid[0:SH, 0:SW].astype(np.float32)
    band = np.clip(1 - np.abs((xs + ys * 0.55) - 420) / 300, 0, 1) * 34
    rgba = np.zeros((SH, SW, 4), np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = band.astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def compose_phone(content):
    scr = Image.new("RGB", (SW, SH), (246, 248, 251))
    scr.paste(content.crop((0, 0, SW, SH - SB)), (0, SB))
    bgc = content.getpixel((5, 5))[:3]
    d = ImageDraw.Draw(scr)
    d.rectangle([0, 0, SW, SB], fill=bgc)
    fg = WHITE if sum(bgc) < 380 else (20, 20, 30)
    d.text((44, 15), "9:41", font=F(24, "SemiBold"), fill=fg)
    d.rounded_rectangle([SW - 84, 20, SW - 44, 37], radius=5, outline=fg, width=2)
    d.rectangle([SW - 80, 24, SW - 54, 33], fill=fg)
    for i in range(4):
        d.rectangle([SW - 134 + i * 10, 33 - i * 5, SW - 128 + i * 10, 37], fill=fg)
    d.rounded_rectangle([SW / 2 - 88, 12, SW / 2 + 88, 48], radius=18, fill=(0, 0, 0))
    scr = scr.convert("RGBA")
    scr.alpha_composite(asset("sheen", make_sheen))
    ph = asset("body", make_body).copy()
    ph.paste(scr, (BZ, BZ), asset("mask", make_mask))
    return ph


D3 = 2400.0


def project(pts, yaw, pitch, roll, s):
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
    out = []
    for x, y in pts:
        X, Y, Z = x - PW / 2, y - PH / 2, 0.0
        X, Y = X * cr - Y * sr, X * sr + Y * cr
        Y, Z = Y * cp - Z * sp, Y * sp + Z * cp
        X, Z = X * cy + Z * sy, -X * sy + Z * cy
        f = D3 / (D3 + Z)
        out.append((X * f * s, Y * f * s))
    return out


def persp_coeffs(dst, src):
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def fpt(cx, cy):
    """content point -> phone image point"""
    return BZ + cx, BZ + SB + cy


CENTER = (PW / 2, PH / 2)


def cam(yaw, pitch, roll, s, focus, target):
    return [yaw, pitch, roll, s, focus[0], focus[1], target[0], target[1]]


def cam_at(a, b, t):
    k = ease(t)
    return [lerp(x, y, k) for x, y in zip(a, b)]


def place_phone(frame, content, c, glow=0.55, min_top=None):
    yaw, pitch, roll, s, fu, fv, tx, ty = c
    corners = [(0, 0), (PW, 0), (PW, PH), (0, PH)]
    pr = project(corners + [(fu, fv)], yaw, pitch, roll, s)
    dx, dy = tx - pr[4][0], ty - pr[4][1]
    dst = [(x + dx, y + dy) for x, y in pr[:4]]
    if min_top is not None:
        top = min(y for _, y in dst)
        if top < min_top:
            dst = [(x, y + min_top - top) for x, y in dst]
    ph = compose_phone(content)
    warped = ph.transform((W, H), Image.PERSPECTIVE, persp_coeffs(dst, corners), Image.BICUBIC)
    a = warped.getchannel("A").resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(16))
    g = Image.new("RGBA", (W // 4, H // 4), (140, 100, 255, 0))
    g.putalpha(a.point(lambda v: int(v * glow)))
    frame.alpha_composite(g.resize((W, H), Image.BILINEAR))
    frame.alpha_composite(warped)


# ---------------------------------------------------------------- phone screen contents (portal UI, sample data)
def canvas(bg=(246, 248, 251)):
    im = Image.new("RGBA", (SW, SH), bg + (255,))
    return im, ImageDraw.Draw(im)


def ct(d, text, fnt, y, fill, x0=0, x1=SW):
    w = d.textlength(text, font=fnt)
    d.text((x0 + (x1 - x0 - w) / 2, y), text, font=fnt, fill=fill)


def header(d):
    d.rectangle([0, 0, SW, 90], fill=NAVY)
    d.text((30, 26), "Minda", font=F(30, "Bold"), fill=WHITE)
    d.text((30 + d.textlength("Minda", font=F(30, "Bold")), 26), "Optima", font=F(30, "Bold"), fill=GOLD)


def field(d, x, y, w, label, value, active=False, caret=False):
    d.text((x, y), label, font=F(22, "SemiBold"), fill=NAVY)
    d.rounded_rectangle([x, y + 34, x + w, y + 98], radius=12, fill=WHITE,
                        outline=NAVY if active else LINE, width=3 if active else 2)
    d.text((x + 20, y + 51), value, font=F(26), fill=DARK)
    if caret:
        cx = x + 22 + d.textlength(value, font=F(26))
        d.line([cx, y + 50, cx, y + 82], fill=NAVY, width=3)


def button(d, box, text, fill, color=WHITE, outline=None, size=26):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=14, fill=fill, outline=outline, width=3 if outline else 0)
    fnt = F(size, "Bold")
    ct(d, text, fnt, y0 + (y1 - y0 - size * 1.2) / 2, color, x0, x1)


def card(d, y0, y1):
    d.rounded_rectangle([24, y0, SW - 24, y1], radius=20, fill=WHITE, outline=LINE, width=2)


def para(d, text, fnt, x, y, maxw, fill, gap=7):
    for ln in wrap(text, fnt, maxw):
        d.text((x, y), ln, font=fnt, fill=fill)
        y += fnt.size + gap
    return y


def ripple(im, x, y, p):
    """tap highlight on screen content, p in [0,1]"""
    if p <= 0 or p >= 1:
        return
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    r = 18 + 70 * eout(p)
    a = int(200 * (1 - p))
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 193, 7, a // 2), outline=(255, 193, 7, a), width=5)
    r2 = 16 * (1 - p * 0.5)
    d.ellipse([x - r2, y - r2, x + r2, y + r2], fill=(255, 255, 255, int(230 * (1 - p))))
    im.alpha_composite(ov)


def typed(text, p):
    return text[:int(round(len(text) * clamp(p)))]


def scr_landing(tap=0.0):
    im, d = canvas()
    d.rectangle([0, 0, SW, 56], fill=GOLD)
    ct(d, "Tawaran terhad sehingga 31 Disember 2026", F(20, "Bold"), 16, NAVY)
    d.rectangle([0, 56, SW, 760], fill=NAVY)
    d.text((30, 84), "Minda", font=F(30, "Bold"), fill=WHITE)
    d.text((30 + d.textlength("Minda", font=F(30, "Bold")), 84), "Optima", font=F(30, "Bold"), fill=GOLD)
    d.rounded_rectangle([140, 168, SW - 140, 212], radius=22, fill=(30, 64, 120))
    ct(d, "Program Rujukan Minda Optima", F(19, "Medium"), 179, WHITE)
    ct(d, "Jemput Kawan,", F(52, "ExtraBold"), 245, WHITE)
    ct(d, "Dapat RM100!", F(52, "ExtraBold"), 312, GOLD)
    y = 405
    for ln in ["Kongsi kod rujukan anda dengan ibu bapa lain.", "Bila mereka daftar, anak mereka dapat 1 kelas",
               "percubaan PERCUMA dan anda dapat RM100", "Touch 'n Go."]:
        ct(d, ln, F(21), y, SOFT)
        y += 32
    button(d, [50, 570, SW - 50, 640], "Daftar sebagai Rujukan", GOLD, NAVY)
    button(d, [50, 662, SW - 50, 732], "Masuk Dashboard", NAVY, WHITE, outline=SOFT)
    ct(d, "Cara Kerja", F(34, "Bold"), 806, NAVY)
    ct(d, "3 langkah mudah je", F(22), 856, GREY)
    for i, (t, sub) in enumerate([("Share Kod", "Dapatkan kod & kongsi di WhatsApp"),
                                  ("Kawan Daftar", "Kawan dapat 1 kelas PERCUMA")]):
        y0 = 916 + i * 150
        card(d, y0, y0 + 130)
        d.text((50, y0 + 22), f"LANGKAH {i + 1}", font=F(18, "Bold"), fill=(200, 140, 0))
        d.text((50, y0 + 50), t, font=F(28, "Bold"), fill=NAVY)
        d.text((50, y0 + 88), sub, font=F(20), fill=GREY)
    ripple(im, 300, 605, tap)
    return im


def scr_login(pn=1.0, en=1.0, tap=0.0):
    im, d = canvas()
    header(d)
    card(d, 130, 760)
    d.text((54, 160), "Log Masuk / Daftar", font=F(36, "Bold"), fill=NAVY)
    d.text((54, 212), "Kami akan hantar kod OTP ke email anda.", font=F(21), fill=GREY)
    typing_phone = 0 < pn < 1
    typing_mail = 0 < en < 1
    field(d, 54, 270, SW - 108, "Nombor Telefon", typed("012-345 6789", pn) or ("" if pn else "01X-XXXXXXX"),
          active=typing_phone, caret=typing_phone)
    para(d, "Pastikan nombor telefon ini betul dan sah, kerana reward Touch 'n Go anda akan dihantar terus ke nombor ini.",
         F(19, "Medium"), 54, 382, SW - 108, (215, 110, 0), 5)
    field(d, 54, 480, SW - 108, "Email", typed("contoh@email.com", en) or ("" if en else "nama@contoh.com"),
          active=typing_mail, caret=typing_mail)
    button(d, [54, 630, SW - 54, 702], "Hantar OTP via Email", NAVY)
    ripple(im, 300, 666, tap)
    return im


def scr_email():
    im, d = canvas()
    d.rectangle([0, 0, SW, 90], fill=(240, 242, 246))
    d.text((30, 28), "<  Peti Masuk", font=F(28, "SemiBold"), fill=DARK)
    d.ellipse([30, 128, 100, 198], fill=NAVY)
    ct(d, "MO", F(26, "Bold"), 147, GOLD, 30, 100)
    d.text((120, 130), "Minda Optima", font=F(28, "Bold"), fill=DARK)
    d.text((120, 170), "kepada saya  ·  baru sahaja", font=F(20), fill=GREY)
    d.text((30, 236), "Kod OTP Minda Optima", font=F(34, "Bold"), fill=DARK)
    d.text((30, 282), "Referral Anda", font=F(34, "Bold"), fill=DARK)
    card(d, 360, 760)
    ct(d, "Kod OTP anda:", F(28, "Medium"), 410, GREY)
    d.rounded_rectangle([90, 470, SW - 90, 590], radius=18, fill=(255, 246, 214), outline=GOLD, width=4)
    ct(d, "847291", F(76, "ExtraBold"), 482, NAVY)
    ct(d, "Kod ini luput dalam 10 minit.", F(22), 630, GREY)
    ct(d, "Jangan kongsi kod ini dengan sesiapa.", F(22), 670, GREY)
    return im


def scr_otp(n=1.0, tap=0.0):
    im, d = canvas()
    header(d)
    card(d, 130, 680)
    d.text((54, 160), "<  Tukar nombor", font=F(21), fill=GREY)
    d.text((54, 206), "Masukkan OTP", font=F(38, "Bold"), fill=NAVY)
    d.text((54, 266), "Kod 6-digit telah dihantar ke", font=F(21), fill=GREY)
    d.text((54, 296), "contoh@email.com.", font=F(21, "Bold"), fill=NAVY)
    d.text((54, 358), "Kod OTP", font=F(22, "SemiBold"), fill=NAVY)
    d.rounded_rectangle([54, 394, SW - 54, 480], radius=12, fill=WHITE, outline=NAVY, width=3)
    digits = typed("847291", n)
    for i in range(6):
        x = 100 + i * 80
        if i < len(digits):
            ct(d, digits[i], F(46, "Bold"), 410, NAVY, x - 30, x + 30)
        else:
            d.line([x - 18, 458, x + 18, 458], fill=LINE, width=3)
    button(d, [54, 520, SW - 54, 592], "Sahkan OTP", NAVY)
    ct(d, "Tak terima kod? Hantar semula", F(20), 622, GREY)
    ripple(im, 300, 556, tap)
    return im


def scr_profile(nn=1.0, jn=1.0, tap=0.0):
    im, d = canvas()
    header(d)
    card(d, 130, 960)
    d.text((54, 160), "Lengkapkan Profil Anda", font=F(34, "Bold"), fill=NAVY)
    d.rounded_rectangle([54, 220, SW - 54, 350], radius=12, fill=(254, 236, 236), outline=(240, 180, 180), width=2)
    para(d, "Penting: Ganjaran RM100 (sehingga 31 Dis 2026), RM50 selepas. Kawan anda mesti DAFTAR dan HADIR KELAS untuk terima reward.",
         F(19, "Medium"), 72, 236, SW - 144, (180, 30, 30), 5)
    field(d, 54, 380, SW - 108, "Nama Penuh", typed("Siti Aminah", nn), active=0 < nn < 1, caret=0 < nn < 1)
    para(d, "Reward akan dihantar ke Touch 'n Go nombor 012-345 6789. Sila sahkan nombor ini betul.",
         F(19), 54, 492, SW - 108, GREY, 5)
    field(d, 54, 580, SW - 108, "Pekerjaan (Pilihan)", typed("Guru", jn), active=0 < jn < 1, caret=0 < jn < 1)
    button(d, [54, 760, SW - 54, 832], "Daftar Sekarang", NAVY)
    ripple(im, 300, 796, tap)
    return im


def dash_header(d):
    d.rectangle([0, 0, SW, 130], fill=NAVY)
    d.text((30, 26), "Selamat Datang,", font=F(22), fill=SOFT)
    d.text((30, 58), "Siti Aminah", font=F(36, "Bold"), fill=WHITE)
    d.text((SW - 190, 48), "Profil   Keluar", font=F(20, "Medium"), fill=SOFT)


def scr_dashboard(code=1.0, tap=0.0, toast=0.0):
    im, d = canvas()
    dash_header(d)
    d.rounded_rectangle([24, 160, SW - 24, 270], radius=16, fill=GOLD)
    d.text((48, 180), "TAWARAN TERHAD: Refer sebelum 31 Dis", font=F(21, "Bold"), fill=NAVY)
    d.text((48, 214), "RM100 TnG! Selepas itu RM50.", font=F(21, "Bold"), fill=NAVY)
    d.rounded_rectangle([24, 300, SW - 24, 560], radius=18, fill=WHITE, outline=NAVY, width=3)
    ct(d, "KOD RUJUKAN ANDA", F(22, "SemiBold"), 330, GREY)
    full = "MO-AB12-CD34"
    shown = typed(full, code)
    fnt = F(50, "ExtraBold")
    x = (SW - d.textlength(full, font=fnt)) / 2
    d.text((x, 374), shown, font=fnt, fill=NAVY)
    button(d, [190, 460, SW - 190, 524], "Copy Kod", NAVY)
    for i, (lab, val) in enumerate([("Bilangan", "0"), ("Pending", "RM0"), ("Total Earned", "RM0")]):
        x0 = 24 + i * 190
        d.rounded_rectangle([x0, 600, x0 + 172, 740], radius=16, fill=WHITE, outline=LINE, width=2)
        ct(d, lab, F(19), 625, GREY, x0, x0 + 172)
        ct(d, val, F(36, "Bold"), 668, NAVY, x0, x0 + 172)
    ripple(im, 300, 492, tap)
    if toast > 0:
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        o = ImageDraw.Draw(ov)
        y = 800 - 30 * eout(toast)
        o.rounded_rectangle([150, y, SW - 150, y + 64], radius=32, fill=(20, 30, 50, int(235 * toast)))
        tw = o.textlength("Kod disalin!", font=F(24, "SemiBold"))
        o.text(((SW - tw) / 2, y + 17), "Kod disalin!", font=F(24, "SemiBold"), fill=(255, 255, 255, int(255 * toast)))
        im.alpha_composite(ov)
    return im


SHARE_MSG = ("Jom daftar kelas membaca Minda Optima! Guna kod MO-AB12-CD34 bila daftar, "
             "anak dapat 1 kelas percubaan PERCUMA. https://referral.mindaoptima.com")


def scr_share(tap=0.0):
    im, d = canvas()
    dash_header(d)
    card(d, 160, 760)
    d.text((54, 184), "Kongsi di WhatsApp", font=F(30, "Bold"), fill=NAVY)
    d.rounded_rectangle([54, 244, SW - 54, 520], radius=14, fill=(226, 247, 230))
    para(d, SHARE_MSG, F(22, "Medium"), 76, 266, SW - 152, (20, 70, 40), 8)
    button(d, [54, 560, SW - 54, 632], "Share ke WhatsApp", (37, 211, 102))
    button(d, [54, 656, SW - 54, 728], "Copy Mesej", WHITE, NAVY, outline=NAVY)
    ripple(im, 300, 596, tap)
    return im


STATUS = {"Menunggu": ((255, 240, 200), (170, 110, 0)), "Layak": ((215, 230, 252), (30, 80, 170)),
          "Dibayar": ((210, 245, 220), (20, 120, 60))}


def scr_status(lt=0.0):
    im, d = canvas()
    dash_header(d)
    card(d, 160, 820)
    d.text((54, 184), "Senarai Rujukan", font=F(30, "Bold"), fill=NAVY)
    for x, h in [(54, "NAMA"), (230, "TARIKH"), (390, "STATUS")]:
        d.text((x, 248), h, font=F(19, "Bold"), fill=GREY)
    d.line([54, 285, SW - 54, 285], fill=LINE, width=2)
    k = "Menunggu" if lt < 1.4 else ("Layak" if lt < 2.6 else "Dibayar")
    flash = max(prog(lt, 1.4, 1.9) * (1 - prog(lt, 1.9, 2.3)), prog(lt, 2.6, 3.1) * (1 - prog(lt, 3.1, 3.5)))
    rows = [("Nurul", "20 Okt", "Dibayar"), ("Faiz", "18 Okt", "Layak"), ("Kumar", "15 Okt", k)]
    for i, (n, t, st) in enumerate(rows):
        y = 308 + i * 120
        if i == 2:
            d.rounded_rectangle([40, y, SW - 40, y + 86], radius=14, fill=(255, 250, 230))
        d.text((54, y + 22), n, font=F(26, "Bold"), fill=DARK)
        d.text((230, y + 24), t, font=F(23), fill=GREY)
        bg, fg = STATUS[st]
        tw = d.textlength(st, font=F(21, "Bold")) + 32
        d.rounded_rectangle([390, y + 16, 390 + tw, y + 62], radius=23, fill=bg,
                            outline=GOLD if (i == 2 and flash > 0.05) else None, width=4)
        d.text((406, y + 25), st, font=F(21, "Bold"), fill=fg)
        d.line([54, y + 100, SW - 54, y + 100], fill=LINE, width=1)
    ct(d, "Menunggu  >  Layak  >  Dibayar", F(24, "Bold"), 700, NAVY)
    return im


# ---------------------------------------------------------------- 2D overlays
def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def text_c(lay, text, fnt, y, fill, alpha=1.0, cx=W / 2):
    d = ImageDraw.Draw(lay)
    d.text((cx, y), text, font=fnt, fill=fill + (int(255 * clamp(alpha)),), anchor="ma")


def text_multi(lay, parts, fnt, y, alpha=1.0, cx=W / 2):
    """parts: [(text, color)], centred as one line"""
    d = ImageDraw.Draw(lay)
    total = sum(d.textlength(t, font=fnt) for t, _ in parts)
    x = cx - total / 2
    for t, c in parts:
        d.text((x, y), t, font=fnt, fill=c + (int(255 * clamp(alpha)),))
        x += d.textlength(t, font=fnt)


def brand(frame, alpha=1.0):
    lay = layer()
    text_multi(lay, [("Minda ", WHITE), ("Optima", GOLD)], F(40, "Bold"), 96, alpha)
    frame.alpha_composite(lay)


def disclaimer(frame):
    lay = layer()
    for i, ln in enumerate(["Tertakluk kepada syarat & ketentuan. Reward dibayar melalui Touch 'n Go",
                            "selepas kawan daftar dan hadir kelas, dan diluluskan."]):
        text_c(lay, ln, F(24), 1828 + i * 36, SOFT, 0.8)
    frame.alpha_composite(lay)


def caption(frame, lt, dur, step, title, detail):
    out = 1 - prog(lt, dur - 0.25, dur)
    lay = layer()
    d = ImageDraw.Draw(lay)
    p1, p2, p3 = eout(prog(lt, 0.05, 0.4)), eout(prog(lt, 0.15, 0.55)), eout(prog(lt, 0.25, 0.7))
    if step:
        fnt = F(34, "Bold")
        sw = d.textlength(step, font=fnt) + 56
        y = 196 + 24 * (1 - p1)
        d.rounded_rectangle([(W - sw) / 2, y, (W + sw) / 2, y + 58], radius=29,
                            fill=GOLD + (int(255 * p1 * out),))
        d.text((W / 2, y + 11), step, font=fnt, fill=NAVY + (int(255 * p1 * out),), anchor="ma")
    text_c(lay, title, F(66, "ExtraBold"), 286 + 28 * (1 - p2), WHITE, p2 * out)
    for i, ln in enumerate(wrap(detail, F(38, "Medium"), 940)):
        text_c(lay, ln, F(38, "Medium"), 384 + i * 52 + 28 * (1 - p3), SOFT, p3 * out)
    frame.alpha_composite(lay)


def glass(d, box, alpha=1.0, radius=36, fill=(255, 255, 255, 34), outline=(255, 255, 255, 110)):
    d.rounded_rectangle(box, radius=radius, fill=fill[:3] + (int(fill[3] * alpha),),
                        outline=outline[:3] + (int(outline[3] * alpha),), width=3)


# ---------------------------------------------------------------- scenes
def base(t):
    fr = background(t)
    return fr


def finish(fr, cap=True):
    fr.alpha_composite(asset("vig", make_vignette))
    return fr


def sc_hook(t, lt, dur):
    fr = base(t)
    # phone rising from the bottom
    p = ease(prog(lt, 2.2, 3.6))
    c = cam(-14, 16, -6, 0.66, CENTER, (560, lerp(2700, 1780, p)))
    if p > 0:
        place_phone(fr, scr_landing(), c)
    fr = finish(fr)
    lay = layer()
    d = ImageDraw.Draw(lay)
    a = eout(prog(lt, 0.0, 0.4))
    text_c(lay, "Parents!", F(130, "Black"), 250 + 40 * (1 - a), GOLD, a)
    b = eout(prog(lt, 0.35, 0.8))
    text_multi(lay, [("Dapatkan ", WHITE), ("RM100", GOLD)], F(92, "ExtraBold"), 430 + 30 * (1 - b), b)
    text_c(lay, "Touch 'n Go", F(92, "ExtraBold"), 540 + 30 * (1 - b), WHITE, b)
    c2 = eout(prog(lt, 0.7, 1.1))
    text_c(lay, "hanya dengan mengajak kawan daftar", F(40, "Medium"), 680 + 20 * (1 - c2), SOFT, c2)
    text_c(lay, "kelas membaca Minda Optima", F(40, "Medium"), 732 + 20 * (1 - c2), SOFT, c2)
    tiles = [("Ajak kawan", "people"), ("Kawan daftar\n& hadir kelas", "check"), ("Dapat RM100\nTouch 'n Go", "rm")]
    for i, (label, icon) in enumerate(tiles):
        q = eout(prog(lt, 1.1 + i * 0.22, 1.5 + i * 0.22))
        if q <= 0:
            continue
        cx = 540 + (i - 1) * 300
        y0 = 850 + 40 * (1 - q)
        glass(d, [cx - 130, y0, cx + 130, y0 + 280], q)
        ic = (cx, y0 + 95)
        col = GOLD + (int(255 * q),)
        if icon == "people":
            for dx, r in [(-26, 22), (26, 22)]:
                d.ellipse([ic[0] + dx - r, ic[1] - 44, ic[0] + dx + r, ic[1]], outline=col, width=6)
                d.arc([ic[0] + dx - 38, ic[1] + 6, ic[0] + dx + 38, ic[1] + 70], 180, 360, fill=col, width=6)
        elif icon == "check":
            d.ellipse([ic[0] - 48, ic[1] - 48, ic[0] + 48, ic[1] + 48], outline=col, width=6)
            d.line([ic[0] - 22, ic[1] + 2, ic[0] - 4, ic[1] + 20, ic[0] + 26, ic[1] - 16], fill=col, width=8)
        else:
            d.ellipse([ic[0] - 48, ic[1] - 48, ic[0] + 48, ic[1] + 48], outline=col, width=6)
            d.text(ic, "RM", font=F(36, "ExtraBold"), fill=col, anchor="mm")
        for j, ln in enumerate(label.split("\n")):
            d.text((cx, y0 + 172 + j * 40), ln, font=F(30, "SemiBold"), fill=WHITE + (int(255 * q),), anchor="ma")
    fr.alpha_composite(lay)
    brand(fr)
    disclaimer(fr)
    return fr


def phone_scene(t, lt, dur, content, c0, c1, step, title, detail):
    fr = base(t)
    place_phone(fr, content, cam_at(c0, c1, lt / dur), min_top=MIN_TOP)
    fr = finish(fr)
    caption(fr, lt, dur, step, title, detail)
    brand(fr)
    disclaimer(fr)
    return fr


PHONE_Y = 1230
MIN_TOP = 500


def sc_landing(t, lt, dur):
    tap = prog(lt, 2.6, 3.4)
    return phone_scene(t, lt, dur, scr_landing(tap),
                       cam(-22, 14, -6, 0.74, CENTER, (540, PHONE_Y)),
                       cam(-8, 8, -3, 1.2, fpt(300, 605), (540, 1180)),
                       "LANGKAH 1", "Buka portal",
                       'Layari referral.mindaoptima.com dan tekan "Daftar sebagai Rujukan"')


def sc_login(t, lt, dur):
    c = scr_login(prog(lt, 0.3, 1.5), prog(lt, 1.7, 3.0), prog(lt, 3.3, 4.0))
    return phone_scene(t, lt, dur, c,
                       cam(18, 12, 5, 1.05, fpt(300, 340), (540, 1100)),
                       cam(8, 6, 2, 1.12, fpt(300, 640), (540, 1150)),
                       "LANGKAH 2", "Isi telefon & email",
                       "Pastikan nombor betul. Reward Touch 'n Go dihantar ke nombor ini")


def sc_email(t, lt, dur):
    fr = base(t)
    place_phone(fr, scr_email(), cam_at(cam(-16, 10, -4, 0.82, CENTER, (540, 1300)),
                                        cam(-6, 6, -2, 0.95, fpt(300, 530), (540, 1250)), lt / dur), min_top=MIN_TOP)
    fr = finish(fr)
    # notification banner
    p = eout(prog(lt, 0.25, 0.75))
    if p > 0:
        lay = layer()
        d = ImageDraw.Draw(lay)
        y = lerp(470, 640, p)
        a = p * (1 - prog(lt, dur - 0.25, dur))
        d.rounded_rectangle([70, y, W - 70, y + 190], radius=36, fill=(248, 249, 255, int(240 * a)),
                            outline=(255, 255, 255, int(255 * a)), width=2)
        d.ellipse([105, y + 38, 185, y + 118], fill=NAVY + (int(255 * a),))
        d.text((145, y + 78), "MO", font=F(30, "ExtraBold"), fill=GOLD + (int(255 * a),), anchor="mm")
        d.text((210, y + 34), "Minda Optima", font=F(32, "Bold"), fill=DARK + (int(255 * a),))
        d.text((W - 110, y + 38), "sekarang", font=F(24), fill=GREY + (int(255 * a),), anchor="ra")
        d.text((210, y + 80), "Kod OTP anda: 847291", font=F(36, "Bold"), fill=NAVY + (int(255 * a),))
        d.text((210, y + 132), "Kod luput dalam 10 minit", font=F(26), fill=GREY + (int(255 * a),))
        fr.alpha_composite(lay)
    caption(fr, lt, dur, "LANGKAH 3", "Semak email anda", "Kod OTP 6 digit dihantar ke email anda dan luput dalam 10 minit")
    brand(fr)
    disclaimer(fr)
    return fr


def sc_otp(t, lt, dur):
    return phone_scene(t, lt, dur, scr_otp(prog(lt, 0.3, 1.6), prog(lt, 2.2, 2.9)),
                       cam(20, 10, 5, 1.05, fpt(300, 437), (540, 1150)),
                       cam(6, 4, 1, 1.25, fpt(300, 540), (540, 1180)),
                       "LANGKAH 4", "Masukkan OTP",
                       'Taip kod 6 digit, kemudian tekan "Sahkan OTP"')


def sc_profile(t, lt, dur):
    c = scr_profile(prog(lt, 0.3, 1.2), prog(lt, 1.4, 1.9), prog(lt, 2.8, 3.5))
    return phone_scene(t, lt, dur, c,
                       cam(-18, 10, -5, 1.05, fpt(300, 446), (540, 1120)),
                       cam(-6, 5, -2, 1.12, fpt(300, 780), (540, 1220)),
                       "LANGKAH 5", "Lengkapkan profil",
                       'Isi nama penuh & pekerjaan (pilihan), kemudian tekan "Daftar Sekarang"')


def sc_dashboard(t, lt, dur):
    c = scr_dashboard(prog(lt, 0.3, 1.0), prog(lt, 2.0, 2.7), prog(lt, 2.4, 2.8))
    return phone_scene(t, lt, dur, c,
                       cam(0, 18, 0, 0.9, fpt(300, 430), (540, 1180)),
                       cam(4, 8, 1, 1.25, fpt(300, 470), (540, 1150)),
                       "DASHBOARD", "Kod rujukan anda",
                       'Siap! Kod unik anda terus terpapar. Tekan "Copy Kod" untuk salin')


def sc_share(t, lt, dur):
    fr = base(t)
    place_phone(fr, scr_share(prog(lt, 1.5, 2.2)), cam_at(cam(16, 10, 4, 1.0, fpt(300, 420), (540, 1180)),
                                                           cam(6, 5, 2, 1.15, fpt(300, 596), (540, 1250)), lt / dur), min_top=MIN_TOP)
    fr = finish(fr)
    p = eout(prog(lt, 2.1, 2.6))
    if p > 0:
        a = p * (1 - prog(lt, dur - 0.25, dur))
        lay = layer()
        d = ImageDraw.Draw(lay)
        y = lerp(980, 820, p)
        lines = wrap(SHARE_MSG, F(30, "Medium"), 720)
        h = 70 + len(lines) * 42
        d.rounded_rectangle([140, y, W - 110, y + h], radius=28, fill=(220, 248, 198, int(245 * a)))
        d.polygon([(W - 110, y + h - 40), (W - 70, y + h), (W - 130, y + h)], fill=(220, 248, 198, int(245 * a)))
        for i, ln in enumerate(lines):
            d.text((175, y + 32 + i * 42), ln, font=F(30, "Medium"), fill=(20, 50, 30, int(255 * a)))
        fr.alpha_composite(lay)
    caption(fr, lt, dur, "DASHBOARD", "Share ke WhatsApp", "Mesej siap dengan kod & link. Terus hantar kepada kawan")
    brand(fr)
    disclaimer(fr)
    return fr


def sc_status(t, lt, dur):
    return phone_scene(t, lt, dur, scr_status(lt),
                       cam(-14, 10, -4, 0.98, fpt(300, 450), (540, 1200)),
                       cam(-4, 5, -1, 1.18, fpt(300, 545), (540, 1200)),
                       "DASHBOARD", "Pantau status rujukan",
                       "Reward dibayar selepas kawan daftar & hadir kelas sebenar")


def sc_terms(t, lt, dur):
    fr = finish(base(t))
    lay = layer()
    d = ImageDraw.Draw(lay)
    out = 1 - prog(lt, dur - 0.25, dur)
    p0 = eout(prog(lt, 0.0, 0.45))
    glass(d, [70, 330 + 40 * (1 - p0), W - 70, 1560 + 40 * (1 - p0)], p0 * out)
    items = [
        (0.2, lambda a, dy: text_c(lay, "SYARAT GANJARAN", F(40, "ExtraBold"), 410 + dy, GOLD, a)),
        (0.4, lambda a, dy: text_c(lay, "Kawan mesti", F(56, "Bold"), 510 + dy, WHITE, a)),
        (0.55, lambda a, dy: text_c(lay, "DAFTAR guna kod anda", F(64, "ExtraBold"), 590 + dy, GOLD, a)),
        (0.7, lambda a, dy: text_c(lay, "+ HADIR KELAS sebenar", F(64, "ExtraBold"), 675 + dy, GOLD, a)),
        (0.85, lambda a, dy: text_c(lay, "Bukan sekadar intro atau isi borang", F(36, "Medium"), 775 + dy, SOFT, a)),
        (1.3, lambda a, dy: text_c(lay, "RM100", F(190, "Black"), 900 + dy, GOLD, a)),
        (1.45, lambda a, dy: text_c(lay, "sehingga 31 Dis 2026", F(52, "Bold"), 1120 + dy, WHITE, a)),
        (1.75, lambda a, dy: text_c(lay, "RM50 selepas itu", F(60, "ExtraBold"), 1260 + dy, WHITE, a)),
        (1.9, lambda a, dy: text_c(lay, "Dibayar melalui Touch 'n Go", F(36, "Medium"), 1360 + dy, SOFT, a)),
    ]
    for start, draw in items:
        q = eout(prog(lt, start, start + 0.4))
        if q > 0:
            draw(q * out, 26 * (1 - q))
    a = eout(prog(lt, 1.6, 2.0)) * out
    d.line([300, 1230, W - 300, 1230], fill=SOFT + (int(120 * a),), width=3)
    fr.alpha_composite(lay)
    brand(fr)
    disclaimer(fr)
    return fr


def sc_end(t, lt, dur):
    fr = base(t)
    p = ease(prog(lt, 0.6, 1.8))
    place_phone(fr, scr_dashboard(), cam(lerp(18, -4, ease(lt / dur)), 12, lerp(6, -2, ease(lt / dur)), 0.62,
                                         CENTER, (540, lerp(2500, 1640, p))))
    fr = finish(fr)
    lay = layer()
    d = ImageDraw.Draw(lay)
    a = eout(prog(lt, 0.0, 0.5))
    text_multi(lay, [("Minda ", WHITE), ("Optima", GOLD)], F(104, "Black"), 230 + 30 * (1 - a), a)
    words, wf, gap = ["Ajak.", "Daftar.", "Dapat RM100."], F(54, "Bold"), 34
    widths = [d.textlength(wd, font=wf) for wd in words]
    x = (W - sum(widths) - gap * (len(words) - 1)) / 2
    for i, wd in enumerate(words):
        q = eout(prog(lt, 0.4 + i * 0.3, 0.8 + i * 0.3))
        col = GOLD if i == 2 else SOFT
        d.text((x, 385 + 20 * (1 - q)), wd, font=wf, fill=col + (int(255 * q),))
        x += widths[i] + gap
    q = eout(prog(lt, 1.3, 1.8))
    text_c(lay, "DAFTAR SEKARANG DI", F(34, "SemiBold"), 520 + 20 * (1 - q), SOFT, q)
    fnt = F(52, "ExtraBold")
    tw = d.textlength("referral.mindaoptima.com", font=fnt) + 80
    y = 590 + 20 * (1 - q)
    d.rounded_rectangle([(W - tw) / 2, y, (W + tw) / 2, y + 96], radius=48, fill=GOLD + (int(255 * q),))
    d.text((W / 2, y + 22), "referral.mindaoptima.com", font=fnt, fill=NAVY + (int(255 * q),), anchor="ma")
    fr.alpha_composite(lay)
    disclaimer(fr)
    return fr


SCENES = [(sc_hook, 4.4), (sc_landing, 4.0), (sc_login, 4.6), (sc_email, 3.6), (sc_otp, 3.4),
          (sc_profile, 4.0), (sc_dashboard, 3.8), (sc_share, 3.8), (sc_status, 4.0), (sc_terms, 4.6),
          (sc_end, 5.2)]
STARTS = [sum(d for _, d in SCENES[:i]) for i in range(len(SCENES))]
TOTAL = sum(d for _, d in SCENES)
TW = 0.2


def whip(img, k, direction):
    """k in (0,1]: strength; direction -1 = move left"""
    arr = np.asarray(img.convert("RGB"), np.float32)
    shift = int(direction * 340 * k * k)
    blur = int(110 * k)
    n = 7
    acc = np.zeros_like(arr)
    for j in range(n):
        acc += np.roll(arr, shift + int(direction * blur * (j / (n - 1) - 0.5)), axis=1)
    return Image.fromarray((acc / n).astype(np.uint8))


def render(i):
    t = i / FPS
    idx = max(j for j, s in enumerate(STARTS) if s <= t + 1e-9)
    fn, dur = SCENES[idx]
    lt = t - STARTS[idx]
    img = fn(t, lt, dur).convert("RGB")
    if idx < len(SCENES) - 1 and lt > dur - TW:
        img = whip(img, (lt - (dur - TW)) / TW, -1)
    elif idx > 0 and lt < TW:
        img = whip(img, 1 - lt / TW, -1)
    return img


def render_bytes(i):
    return render(i).tobytes()


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        out = sys.argv[2]
        for tt in sys.argv[3:]:
            render(int(float(tt) * FPS)).save(f"{out}/still_{float(tt):05.1f}.png")
    else:
        out = sys.argv[2]
        n = int(round(TOTAL * FPS))
        ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                               "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for k, b in enumerate(pool.imap(render_bytes, range(n), chunksize=4)):
                ff.stdin.write(b)
                if k % 150 == 0:
                    print(f"frame {k}/{n}", flush=True)
        ff.stdin.close()
        ff.wait()
        print("total", TOTAL)
