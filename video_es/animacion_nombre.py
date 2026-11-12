"""Animación «Allah nunca lo llamó por su nombre» (1080x1920): textos árabes con su significado en español y marca «Casa Antigua».

Uso: python3 animacion_flat.py <video_o_audio_original> <salida.mp4> [segundo_preview]
"""
import math, subprocess, sys
import cairo

SRC = sys.argv[1]
OUT = sys.argv[2]
PREVIEW = float(sys.argv[3]) if len(sys.argv) > 3 else None
W, H, FPS = 1080, 1920, 30
SPEECH_END = 112.0
END_CARD = 4.0
TOTAL = SPEECH_END + END_CARD

def hx(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) / 255 for i in (0, 2, 4))

BG = hx("F4EBDD"); PANEL = hx("FBF6EE"); NAVY = hx("1F3A4D"); TEAL = hx("2A7F7A")
TERRA = hx("C8603C"); SAND = hx("E3B964"); OLIVE = hx("7E8B4F"); CREAM = hx("FFFDF8")
SKY = hx("CFE3E0"); RED = hx("D2453A"); BROWN = hx("8A5A3B"); GREY = hx("B9B2A6")
SKIN = hx("D9A47E")

SUBS = []

# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x):
    x = clamp(x); c = 1.7; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, k): return a + (b - a) * k

def rrect(c, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    c.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    c.close_path()

def fill(c, col, a=1.0): c.set_source_rgba(*col, a); c.fill()
def circle(c, x, y, r, col, a=1.0):
    c.new_path(); c.arc(x, y, r, 0, 2 * math.pi); fill(c, col, a)
def line(c, x1, y1, x2, y2, w, col, a=1.0):
    c.new_path(); c.set_line_width(w); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(x1, y1); c.line_to(x2, y2); c.set_source_rgba(*col, a); c.stroke()

def font(c, size, bold=True):
    c.select_font_face("Inter", cairo.FONT_SLANT_NORMAL,
                       cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(size)

def text_c(c, s, x, y, size, col, a=1.0, bold=True):
    font(c, size, bold); e = c.text_extents(s)
    c.move_to(x - e.x_advance / 2, y); c.set_source_rgba(*col, a); c.show_text(s)
    return e.x_advance

class pop:
    """Escala/opacidad alrededor de (x, y) para que un elemento 'aparezca'."""
    def __init__(self, c, x, y, k, a=1.0):
        self.c, self.x, self.y, self.k, self.a = c, x, y, k, a
    def __enter__(self):
        c = self.c; c.save(); c.push_group()
        s = 0.001 + back(self.k)
        c.translate(self.x, self.y); c.scale(s, s); c.translate(-self.x, -self.y)
        return c
    def __exit__(self, *a):
        c = self.c; c.pop_group_to_source(); c.paint_with_alpha(clamp(ease(self.k * 1.6)) * self.a); c.restore()

def person(c, x, feet, h, body, wave=0.0, point=0.0, lean=0.0, chest=1.0, head_tilt=0.0, cap=None):
    """Figura sin rostro (estilo flat)."""
    hr = h * 0.12
    c.save(); c.translate(x, feet); c.rotate(lean)
    bw = h * 0.36 * chest; bh = h * 0.5
    # piernas
    line(c, -h * 0.08, -h * 0.3, -h * 0.09, -h * 0.02, h * 0.09, NAVY)
    line(c, h * 0.08, -h * 0.3, h * 0.09, -h * 0.02, h * 0.09, NAVY)
    # cuerpo (túnica)
    c.new_path()
    c.move_to(-bw / 2, -h * 0.28); c.line_to(bw / 2, -h * 0.28)
    c.curve_to(bw / 2, -h * 0.55, bw * 0.4, -h * 0.76, 0, -h * 0.76)
    c.curve_to(-bw * 0.4, -h * 0.76, -bw / 2, -h * 0.55, -bw / 2, -h * 0.28)
    fill(c, body)
    # brazos
    sy = -h * 0.66
    ang_r = lerp(0.3, 2.6, wave) + (0.35 * math.sin(wave * 12) if wave > 0.5 else 0)
    ang_r = lerp(ang_r, 1.6, point)
    ax = bw * 0.42; L = h * 0.3
    line(c, ax, sy, ax + math.sin(ang_r) * L, sy + math.cos(ang_r) * L, h * 0.075, body)
    line(c, -ax, sy, -ax - h * 0.08, sy + h * 0.29, h * 0.075, body)
    # cabeza
    c.save(); c.translate(0, -h * 0.76 - hr * 0.95); c.rotate(head_tilt)
    circle(c, 0, 0, hr, SKIN)
    if cap:
        c.new_path(); c.arc(0, -hr * 0.15, hr * 1.02, math.pi, 2 * math.pi); fill(c, cap)
    c.restore()
    c.restore()

def bubble(c, x, y, w, h, txt, col, tcol, size, tail=-1):
    rrect(c, x - w / 2, y - h / 2, w, h, h * 0.4); fill(c, col)
    c.new_path(); tx = x + tail * w * 0.22
    c.move_to(tx - 18, y + h / 2 - 2); c.line_to(tx + 18, y + h / 2 - 2); c.line_to(tx - tail * 4, y + h / 2 + 34); c.close_path(); fill(c, col)
    text_c(c, txt, x, y + size * 0.36, size, tcol)

# ---------------------------------------------------------------- escenas
PX, PY, PW, PH = 60, 380, 960, 1000
CX, CY = PX + PW / 2, PY + PH / 2
GROUND = PY + PH - 170

def ground(c, col=OLIVE):
    rrect(c, PX, GROUND, PW, PY + PH - GROUND, 0); fill(c, col, 0.25)

import os, io, random
from PIL import Image as _PImage, ImageDraw as _PDraw, ImageFont as _PFont
HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = cairo.ImageSurface.create_from_png(os.path.join(HERE, "logo_casa_antigua.png"))
_AR_FONT = os.path.join(HERE, "fuentes", "Amiri-Bold.ttf")

BG0 = hx("0D2E29"); BG1 = hx("041311"); GOLD = hx("D8B66A"); GOLD2 = hx("F2DDA0"); TEALL = hx("6FC7B4")
CRM = hx("EFE7D4"); MUTED = hx("8FB3A9")

_cache = {}
def AR(txt, size, col=CRM, maxw=900):
    key = (txt, size, col, maxw)
    if key in _cache: return _cache[key]
    f = _PFont.truetype(_AR_FONT, size, layout_engine=_PFont.Layout.RAQM)
    words = txt.split(); lines = [[]]
    for w in words:
        test = " ".join(lines[-1] + [w])
        if lines[-1] and f.getlength(test, direction="rtl") > maxw: lines.append([w])
        else: lines[-1].append(w)
    lines = [" ".join(l) for l in lines]
    lh = int(size * 1.8); wmax = int(max(f.getlength(l, direction="rtl") for l in lines)) + 40
    im = _PImage.new("RGBA", (wmax, lh * len(lines) + int(size * 0.6)), (0, 0, 0, 0)); d = _PDraw.Draw(im)
    rgb = tuple(int(v * 255) for v in col)
    for i, l in enumerate(lines):
        lw = f.getlength(l, direction="rtl")
        d.text(((wmax - lw) / 2, int(size * 0.15) + i * lh), l, font=f, fill=rgb + (255,), direction="rtl", language="ar")
    buf = io.BytesIO(); im.save(buf, "PNG"); buf.seek(0)
    s = cairo.ImageSurface.create_from_png(buf); _cache[key] = s; return s

def blit(c, surf, x, y, a=1.0, scale=1.0, anchor="c"):
    c.save(); c.translate(x, y); c.scale(scale, scale)
    ox = -surf.get_width() / 2 if anchor == "c" else (-surf.get_width() if anchor == "r" else 0)
    c.set_source_surface(surf, ox, -surf.get_height() / 2)
    c.get_source().set_filter(cairo.FILTER_BEST); c.paint_with_alpha(a); c.restore()

def ar(c, txt, x, y, size, col=CRM, a=1.0, maxw=900, anchor="c", glow=0.0):
    if a <= 0.001: return
    s = AR(txt, size, col, maxw)
    if glow > 0:
        for r in (1.04, 1.08):
            blit(c, AR(txt, size, GOLD2, maxw), x, y, a * glow * 0.12, r, anchor)
    blit(c, s, x, y, a, 1.0, anchor)

def es(c, txt, x, y, size, col=CRM, a=1.0, maxw=900, bold=True):
    """Texto en español centrado, con ajuste de línea."""
    if a <= 0.001: return
    txt = txt.replace(" ﷺ?", "?").replace(" ﷺ:", " (la paz sea con él):").replace(" ﷺ", " (la paz sea con él)").replace("ﷺ", "")
    font(c, size, bold); words = txt.split(); lines = [[]]
    for w in words:
        test = " ".join(lines[-1] + [w])
        if lines[-1] and c.text_extents(test).x_advance > maxw: lines.append([w])
        else: lines[-1].append(w)
    for i, l in enumerate(lines):
        text_c(c, " ".join(l), x, y + i * size * 1.3, size, col, a, bold)
    return len(lines)

def fade(T, s, e, fi=0.5, fo=0.4):
    return clamp(min((T - s) / fi, (e - T) / fo))

# ------------------------------------------------------------ fondo
_rng = random.Random(3)
DUST = [(_rng.uniform(0, W), _rng.uniform(0, H), _rng.uniform(1, 3), _rng.uniform(0, 1)) for _ in range(90)]
def background(c, t, stars=0.0):
    g = cairo.RadialGradient(W / 2, 760, 40, W / 2, 900, 1300)
    g.add_color_stop_rgb(0, *BG0); g.add_color_stop_rgb(1, *BG1)
    c.rectangle(0, 0, W, H); c.set_source(g); c.fill()
    for i in range(7):  # haces de luz desde arriba
        a = -0.5 + i * 0.16 + 0.02 * math.sin(t * 0.4 + i)
        c.new_path(); c.move_to(W / 2 + math.sin(a) * 40, -40)
        c.line_to(W / 2 + math.sin(a) * 1900 - 70, 1900); c.line_to(W / 2 + math.sin(a) * 1900 + 70, 1900); c.close_path()
        c.set_source_rgba(*TEALL, 0.025); c.fill()
    for x, y, r, ph in DUST:
        k = (t * 0.03 + ph) % 1
        circle(c, x, (y - k * 300) % H, r, GOLD2, 0.25 * math.sin(k * math.pi))
    if stars > 0:
        for i, (x, y, r, ph) in enumerate(DUST * 3):
            circle(c, (x * 1.7 + i * 37) % W, (y * 1.3 + i * 53) % H, r * 0.7, CRM, stars * (0.3 + 0.5 * abs(math.sin(t + i))))

def header(c, ar_txt, es_txt, a, sub_ar=None, sub_es=None):
    ar(c, ar_txt, W / 2, 300, 62, GOLD2, a)
    es(c, es_txt, W / 2, 400, 40, CRM, a)
    if sub_es:
        es(c, sub_es, W / 2, 455, 30, MUTED, a, bold=False)

def gold_ring(c, x, y, r, a=1.0, lw=4, col=GOLD):
    c.new_path(); c.arc(x, y, r, 0, 2 * math.pi); c.set_line_width(lw); c.set_source_rgba(*col, a); c.stroke()

def dot(c, x, y, r, a=1.0, glow=0.0):
    if glow > 0:
        g = cairo.RadialGradient(x, y, 0, x, y, r * 6)
        g.add_color_stop_rgba(0, *GOLD2, 0.6 * glow * a); g.add_color_stop_rgba(1, *GOLD2, 0)
        c.new_path(); c.arc(x, y, r * 6, 0, 2 * math.pi); c.set_source(g); c.fill()
    circle(c, x, y, r, GOLD2, a)

# ------------------------------------------------------------ 1) órbita de los 25 profetas
PROPHETS = ["آدم", "إدريس", "نوح", "هود", "صالح", "إبراهيم", "لوط", "إسماعيل", "إسحاق", "يعقوب", "يوسف", "أيوب",
            "شعيب", "موسى", "هارون", "ذو الكفل", "داود", "سليمان", "إلياس", "اليسع", "يونس", "زكريا", "يحيى", "عيسى"]
CALLED = {"آدم", "نوح", "إبراهيم", "موسى", "داود", "زكريا", "يحيى", "عيسى"}
OX, OY = W / 2, 1000

def orbit_pos(i):
    if i < 14: r, a0, n = 400, -math.pi / 2 + 0.25, 14
    else: r, a0, n = 260, -math.pi / 2 + 0.2, 10
    j = i if i < 14 else i - 14
    a = a0 + j * 2 * math.pi / n
    return OX + math.cos(a) * r, OY + math.sin(a) * r, r, a

def sc_orbit(c, T):
    a_head = fade(T, 0, 4.0, 0.6, 0.3)
    header(c, "خَمْسَةٌ وَعِشْرُونَ نَبِيًّا", "25 profetas", a_head, sub_es="mencionados por su nombre en el Corán")
    a2 = fade(T, 4.0, 8.6, 0.4, 0.4)
    header(c, "نَادَى اللهُ ثَمَانِيَةً مِنْهُمْ", "Allah llamó a ocho de ellos", a2, sub_es="directamente por su nombre")
    draw = clamp(T / 3.0)
    for r in (400, 260):
        c.new_path(); c.arc(OX, OY, r, -math.pi / 2, -math.pi / 2 + 2 * math.pi * draw); c.set_line_width(3); c.set_source_rgba(*GOLD, 0.7 * (1 - clamp((T - 8) / 0.6))); c.stroke()
    hl = clamp((T - 5.0) / 0.8)
    out = 1 - clamp((T - 8.0) / 0.6)
    for i, name in enumerate(PROPHETS):
        k = clamp((T - i * 0.11) / 0.5)
        if k <= 0: continue
        x, y, r, a = orbit_pos(i)
        called = name in CALLED
        alpha = k * out * (1 - 0.65 * hl * (0 if called else 1))
        dot(c, x, y, 8 if not called else 8 + 4 * hl, alpha, glow=hl if called else 0)
        lx, ly = OX + math.cos(a) * (r + 62), OY + math.sin(a) * (r + 62) + 10
        if i >= 14: lx, ly = OX + math.cos(a) * (r - 70), OY + math.sin(a) * (r - 70) + 10
        ar(c, name, lx, ly, 34 if not (called and hl > 0) else 34 + 6 * hl, GOLD2 if called and hl > 0 else CRM, alpha)
    # centro: Muhammad ﷺ, sello de los profetas
    kc = clamp((T - 3.6) / 0.6) * out
    if kc > 0:
        gold_ring(c, OX, OY, 120, kc); gold_ring(c, OX, OY, 100, 0.5 * kc, 2)
        ar(c, "مُحَمَّدٌ ﷺ", OX, OY - 14, 48, GOLD2, kc)
        es(c, "Sello de los profetas", OX, OY + 50, 24, TEALL, kc)

# ------------------------------------------------------------ 2) lista de llamadas directas
CALLS = [  # (aparición, árabe, referencia, español, veces)
    (9.0, "يَا آدَمُ أَنْبِئْهُم بِأَسْمَائِهِمْ", "Al-Baqara 2:33", "«¡Oh Adam! Infórmales de sus nombres»", 4),
    (11.5, "يَا نُوحُ اهْبِطْ بِسَلَامٍ مِّنَّا", "Hud 11:48", "«¡Oh Nuh! Desciende con paz de Nuestra parte»", 2),
    (14.0, "يَا إِبْرَاهِيمُ قَدْ صَدَّقْتَ الرُّؤْيَا", "As-Saffat 37:104-105", "«¡Oh Ibrahim! Ya has cumplido la visión»", 1),
    (17.0, "يَا مُوسَىٰ إِنِّي اصْطَفَيْتُكَ عَلَى النَّاسِ", "Al-A'raf 7:144", "«¡Oh Musa! Te he elegido por encima de la gente»", 11),
    (20.0, "يَا دَاوُودُ إِنَّا جَعَلْنَاكَ خَلِيفَةً فِي الْأَرْضِ", "Sad 38:26", "«¡Oh Dawud! Te hemos hecho sucesor en la tierra»", 1),
    (23.5, "يَا زَكَرِيَّا إِنَّا نُبَشِّرُكَ بِغُلَامٍ", "Maryam 19:7", "«¡Oh Zakariya! Te anunciamos un hijo»", 1),
    (27.0, "يَا يَحْيَىٰ خُذِ الْكِتَابَ بِقُوَّةٍ", "Maryam 19:12", "«¡Oh Yahya! Toma la Escritura con firmeza»", 1),
    (30.0, "يَا عِيسَى ابْنَ مَرْيَمَ اذْكُرْ نِعْمَتِي عَلَيْكَ", "Al-Ma'ida 5:110", "«¡Oh 'Isa, hijo de Maryam! Recuerda Mi favor sobre ti»", 3),
]
AR_DIG = "٠١٢٣٤٥٦٧٨٩"
def ad(n): return "".join(AR_DIG[int(ch)] for ch in str(n))

def sc_calls(c, T):
    a = fade(T, 8.4, 35.0, 0.5, 0.6)
    header(c, "نَادَى اللهُ ثَمَانِيَةً مِنْهُمْ", "Allah llamó a ocho de ellos por su nombre", a)
    es(c, "veces", 110, 520, 24, MUTED, a, bold=False)
    cur = max([i for i, x in enumerate(CALLS) if T >= x[0]] + [-1])
    for i, (st, txt, ref, mean, n) in enumerate(CALLS):
        y = 590 + i * 112
        k = clamp((T - st) / 0.5)
        active = i == cur
        al = a * (0.35 + 0.65 * k)
        sz = 44 if not active else 50
        ar(c, txt, W - 90, y, sz, GOLD2 if active else CRM, al, maxw=900, anchor="r", glow=1 if active else 0)
        if k > 0:
            with pop(c, 110, y, k, a):
                if active: gold_ring(c, 110, y, 38, 0.8)
                ar(c, ad(n), 110, y, 46, GOLD2, 1)
    # significado del llamado activo
    if 0 <= cur and T < 33.6:
        st, txt, ref, mean, n = CALLS[cur]
        k = clamp((T - st) / 0.5) * a
        rrect(c, 70, 1520, W - 140, 250, 36); fill(c, BG1, 0.75 * k)
        es(c, mean, W / 2, 1600, 42, CRM, k, 880)
        es(c, ref + f"  ·  {n} {'vez' if n == 1 else 'veces'}", W / 2, 1735, 28, GOLD, k, 880, bold=False)
    # aparece Muhammad ﷺ
    if T > 33.6:
        k = clamp((T - 33.6) / 0.6) * a
        ar(c, "مُحَمَّدٌ ﷺ", W / 2, 1640, 70, GOLD2, k, glow=1)
        es(c, "¿Y Muhammad ﷺ?", W / 2, 1760, 40, CRM, k)

# ------------------------------------------------------------ 3) «Di» más de 300 veces
def sc_qul(c, T):
    a = fade(T, 35.2, 44.0, 0.5, 0.5)
    if T < 42.0:
        header(c, "وَيَقُولُ اللهُ لِمُحَمَّدٍ ﷺ", "Y Allah le dice a Muhammad ﷺ:", a * fade(T, 35.2, 42.2, 0.5, 0.3))
    else:
        k = clamp((T - 42.0) / 0.4) * a
        header(c, "أَمَّا أَنْ يُنَادِيَهُ بِاسْمِهِ...", "Pero llamarlo por su nombre…", k, sub_es="no ocurrió ni una sola vez")
    cx, cy = W / 2, 760
    gold_ring(c, cx, cy, 110, a); ar(c, "مُحَمَّدٌ ﷺ", cx, cy - 4, 50, GOLD2, a)
    # rejilla de «Di» que se ilumina
    gx, gy, gw, gh = 110, 1150, W - 220, 470
    rrect(c, gx, gy, gw, gh, 16); fill(c, BG1, 0.6 * a)
    c.new_path(); rrect(c, gx, gy, gw, gh, 16); c.set_line_width(2); c.set_source_rgba(*TEALL, 0.4 * a); c.stroke()
    n = int(clamp((T - 36.6) / 3.6) * 332)
    rng = random.Random(11)
    cells = [(rng.random(), rng.random()) for _ in range(332)]
    for i, (u, v) in enumerate(cells[:n]):
        dot(c, gx + 20 + u * (gw - 40), gy + 20 + v * (gh - 40), 3.5, a * 0.9)
    # rayos del centro a la rejilla mientras cuenta
    if 36.6 < T < 40.4:
        for i in range(10):
            u, v = cells[(n - 1 - i * 7) % max(1, n)] if n else (0.5, 0.5)
            line(c, cx, cy + 110, gx + 20 + u * (gw - 40), gy + 20 + v * (gh - 40), 2, GOLD2, 0.5 * a)
    shown = min(300, int(clamp((T - 36.6) / 3.6) * 300))
    lab = ("+" if T > 40.2 else "") + ad(shown)
    rx = W / 2 + (230 if T > 42.0 else 0)
    ar(c, "«قُلْ»", rx, 940, 44, TEALL, a)
    ar(c, lab, rx, 1030, 84, GOLD2, a)
    es(c, "«Di»: más de 300 veces" if T > 40.2 else "«Di»", rx, 1110, 30, CRM, a)
    if T > 42.0:
        k = clamp((T - 42.0) / 0.4) * a
        line(c, W / 2, 900, W / 2, 1110, 2, GOLD, k)
        lx = W / 2 - 230
        ar(c, "«يَا مُحَمَّدُ»", lx, 940, 44, TEALL, k)
        gold_ring(c, lx, 1030, 50, k, 3); ar(c, ad(0), lx, 1030, 60, GOLD2, k)
        es(c, "«¡Oh Muhammad!»: 0 veces", lx, 1110, 30, CRM, k)

# ------------------------------------------------------------ 4) los llamados por atributo
TITLES = [  # inicio, fin, árabe, español, explicación, veces
    (45.5, 47.6, "يَا أَيُّهَا النَّبِيُّ", "«¡Oh Profeta!»", "llamada de profecía y honra", 13),
    (47.6, 51.0, "يَا أَيُّهَا الرَّسُولُ", "«¡Oh Mensajero!»", "llamada del mensaje y la transmisión", 2),
    (51.0, 53.2, "يَا أَيُّهَا الْمُزَّمِّلُ", "«¡Oh tú, el envuelto en su manto!»", "el que se envuelve en su ropa", 1),
    (53.2, 55.3, "يَا أَيُّهَا الْمُدَّثِّرُ", "«¡Oh tú, el arropado!»", "el que se cubre con su manto", 1),
]
def sc_titles(c, T):
    a = fade(T, 44.2, 59.0, 0.6, 0.5)
    header(c, "بَلْ يَقُولُ اللهُ:", "Sino que Allah dice:", a)
    if T < 55.3:
        for s, e, txt, sp, exp, n in TITLES:
            if not (s <= T < e): continue
            k = fade(T, s, e, 0.4, 0.3) * a
            cx, cy = W / 2, 1000
            for j in range(48):
                ang = j * math.pi / 24 + T * 0.2
                L = 30 + 20 * math.sin(T * 3 + j)
                line(c, cx + math.cos(ang) * 330, cy + math.sin(ang) * 330, cx + math.cos(ang) * (330 + L), cy + math.sin(ang) * (330 + L), 3, GOLD, 0.5 * k)
            gold_ring(c, cx, cy, 300, k, 3); gold_ring(c, cx, cy, 280, 0.4 * k, 1)
            with pop(c, cx, cy, (T - s) / 0.5, a):
                ar(c, txt, cx, cy - 50, 92, CRM, 1, glow=1)
                es(c, sp, cx, cy + 70, 36, GOLD2, 1, 520)
                es(c, exp, cx, cy + 165 if len(sp) > 22 else cy + 120, 26, MUTED, 1, 520, bold=False)
            ar(c, ad(n), cx, 1380, 80, GOLD2, k)
            es(c, f"{n} {'vez' if n == 1 else 'veces'}", cx, 1460, 30, CRM, k)
    else:
        k = clamp((T - 55.3) / 0.5) * a
        for i, (s, e, txt, sp, exp, n) in enumerate(TITLES):
            y = 700 + i * 150
            kk = clamp((T - 55.3 - i * 0.15) / 0.4) * a
            ar(c, txt, W - 120, y, 56, CRM, kk, anchor="r")
            line(c, 300, y, 520, y, 2, GOLD, kk)
            ar(c, ad(n), 200, y, 52, GOLD2, kk)
            es(c, sp, W / 2 + 120, y + 70, 26, MUTED, kk, bold=False)
        es(c, "17 llamadas por sus atributos…", W / 2, 1360, 40, GOLD2, k)
        es(c, "y ninguna por su nombre", W / 2, 1420, 40, CRM, k)

# ------------------------------------------------------------ 5) aleyas
def ayah_block(c, T, s, e, txt, ref, mean, y=950, size=70, hl=None):
    k = fade(T, s, e, 0.6, 0.5)
    if k <= 0: return
    g = cairo.RadialGradient(W / 2, y, 10, W / 2, y, 520)
    g.add_color_stop_rgba(0, *GOLD2, 0.12 * k); g.add_color_stop_rgba(1, *GOLD2, 0)
    c.rectangle(0, y - 520, W, 1040); c.set_source(g); c.fill()
    ar(c, txt, W / 2, y, size, CRM, k, maxw=920, glow=0.6)
    es(c, ref, W / 2, y + 190, 26, GOLD, k, bold=False)
    es(c, mean, W / 2, y + 280, 40, CRM, k, 900)

def sc_ayat(c, T):
    a = fade(T, 59.0, 66.0, 0.4, 0.4)
    header(c, "بَلْ يَقُولُ اللهُ:", "Sino que Allah dice:", a)
    ayah_block(c, T, 59.2, 61.6, "يَا أَيُّهَا النَّبِيُّ حَسْبُكَ اللهُ", "Al-Anfal 8:64", "«¡Oh Profeta! Allah te basta»")
    ayah_block(c, T, 61.6, 66.0, "يَا أَيُّهَا النَّبِيُّ إِنَّا أَرْسَلْنَاكَ شَاهِدًا وَمُبَشِّرًا وَنَذِيرًا وَدَاعِيًا إِلَى اللهِ بِإِذْنِهِ وَسِرَاجًا مُنِيرًا",
               "Al-Ahzab 33:45-46", "«¡Oh Profeta! Te hemos enviado como testigo, portador de buenas nuevas y advertidor, que llama a Allah con Su permiso, y como lámpara luminosa»", y=880, size=58)
    a2 = fade(T, 66.4, 73.0, 0.6, 0.6)
    header(c, "وَيَقُولُ اللهُ لَهُ:", "Y Allah le dice:", a2)
    ayah_block(c, T, 67.2, 73.0, "وَرَفَعْنَا لَكَ ذِكْرَكَ", "Ash-Sharh 94:4", "«Y elevamos tu mención»", size=96)

# ------------------------------------------------------------ 6) el adhán recorre la Tierra
_rg = random.Random(5)
LAND = [(_rg.uniform(-1, 1), _rg.uniform(-0.9, 0.9)) for _ in range(900)]
def land(lon, lat):  # continentes abstractos por manchas
    blobs = [(0.35, 0.10, 0.30, 0.38), (0.55, -0.45, 0.16, 0.22), (0.25, 0.88, 0.32, 0.12), (0.80, 0.42, 0.14, 0.15),
             (1.55, 0.85, 0.80, 0.22), (1.85, 0.50, 0.42, 0.22), (1.37, 0.32, 0.10, 0.17), (1.90, 0.18, 0.12, 0.14),
             (2.35, -0.45, 0.26, 0.15), (-1.75, 0.85, 0.55, 0.25), (-1.60, 0.55, 0.30, 0.22), (-1.05, -0.25, 0.20, 0.42), (-0.75, 1.25, 0.25, 0.12)]
    return any(((lon - bx) / bw) ** 2 + ((lat - by) / bh) ** 2 < 1 for bx, by, bw, bh in blobs)
_rg2 = random.Random(9)
PTS = [(_rg2.uniform(-math.pi, math.pi), math.asin(_rg2.uniform(-1, 1))) for _ in range(24000)]
PTS = [(lo, la) for lo, la in PTS if land(lo, la)]

def globe(c, cx, cy, R, rot, sweep, a, T):
    g = cairo.RadialGradient(cx - R * 0.3, cy - R * 0.3, R * 0.1, cx, cy, R)
    g.add_color_stop_rgba(0, *hx("1F5E55"), a); g.add_color_stop_rgba(1, *hx("06201C"), a)
    c.new_path(); c.arc(cx, cy, R, 0, 2 * math.pi); c.set_source(g); c.fill()
    for i in range(3): gold_ring(c, cx, cy, R + 8 + i * 10, a * (0.35 - i * 0.1), 6, TEALL)
    c.save(); c.new_path(); c.arc(cx, cy, R, 0, 2 * math.pi); c.clip()
    for lo, la in PTS:
        l = lo + rot
        z = math.cos(la) * math.cos(l)
        if z < 0: continue
        x = cx + R * math.cos(la) * math.sin(l); y = cy - R * math.sin(la)
        circle(c, x, y, 2.6, hx("A9E3CF"), a * (0.35 + 0.65 * z))
    # ola del adhán: meridiano brillante que avanza
    l = sweep
    for w_, al in ((26, 0.12), (12, 0.3), (4, 0.9)):
        c.new_path()
        for j in range(61):
            la = -math.pi / 2 + j * math.pi / 60
            z = math.cos(la) * math.cos(l)
            x = cx + R * math.cos(la) * math.sin(l); y = cy - R * math.sin(la)
            (c.move_to if j == 0 else c.line_to)(x, y)
        c.set_line_width(w_); c.set_source_rgba(*GOLD2, al * a * (1 if math.cos(l) > 0 else 0)); c.stroke()
    # Meca
    ml = 0.7 + rot
    if math.cos(ml) > 0:
        dot(c, cx + R * math.cos(0.37) * math.sin(ml), cy - R * math.sin(0.37), 6, a, glow=1)
    c.restore()

def sc_adhan(c, T):
    a = fade(T, 73.0, 91.0, 1.0, 1.0)
    rise = ease((T - 73.0) / 2.0) * (1 - ease((T - 89.5) / 1.5) * 0.6)
    cy = 1900 - 650 * rise
    sweep = 1.4 - ((T - 74.0) / 4.0 % 1) * 2.8
    globe(c, W / 2, cy + 120, 430, -0.75 + (T - 73) * 0.015, sweep, a, T)
    labels = ["الفجر", "الظهر", "العصر", "المغرب", "العشاء"]
    es_l = ["Fajr", "Dhuhr", "Asr", "Magrib", "Isha"]
    idx = int(((T - 74.0) / 4.0)) % 5
    if T > 75:
        ar(c, labels[idx], W / 2 + 360, cy - 380, 44, GOLD2, a); es(c, es_l[idx], W / 2 + 360, cy - 320, 28, CRM, a, bold=False)
    a1 = fade(T, 75.5, 82.0, 0.6, 0.4) * a
    header(c, "خَمْسَ مَرَّاتٍ كُلَّ يَوْمٍ...", "Cinco veces al día…", a1, sub_es="una ola de adhán recorre la Tierra")
    a2 = fade(T, 82.0, 90.5, 0.6, 0.6) * a
    header(c, "وَكُلُّ مَوْجَةٍ تَحْمِلُ اسْمَهُ", "y cada ola lleva su nombre", a2)
    ar(c, "مُحَمَّدٌ ﷺ", W / 2, 560, 76, GOLD2, a2, glow=1)
    ar(c, "«أَشْهَدُ أَنَّ مُحَمَّدًا رَسُولُ اللهِ»", W / 2, 680, 44, TEALL, a2)
    es(c, "«Atestiguo que Muhammad es el Mensajero de Allah»", W / 2, 760, 32, CRM, a2, 900)

# ------------------------------------------------------------ 7) 33:56 y salawat
def sc_salawat(c, T):
    a = fade(T, 90.5, 104.0, 0.8, 0.8)
    globe(c, W / 2, 2050, 620, -0.75 + (T - 73) * 0.015, 1.4 - ((T - 74.0) / 4.0 % 1) * 2.8, a * 0.8, T)
    k = fade(T, 91.2, 104.0, 0.8, 0.8)
    ar(c, "إِنَّ اللهَ وَمَلَائِكَتَهُ يُصَلُّونَ عَلَى النَّبِيِّ يَا أَيُّهَا الَّذِينَ آمَنُوا صَلُّوا عَلَيْهِ وَسَلِّمُوا تَسْلِيمًا", W / 2, 520, 60, CRM, k, maxw=940, glow=0.6)
    es(c, "Al-Ahzab 33:56", W / 2, 700, 26, GOLD, k, bold=False)
    es(c, "«Allah y Sus ángeles bendicen al Profeta. ¡Oh creyentes! Pedid bendiciones por él y saludadle con un saludo de paz»", W / 2, 790, 38, CRM, k, 920)
    k2 = fade(T, 95.5, 104.0, 0.8, 0.8)
    ar(c, "اللَّهُمَّ صَلِّ وَسَلِّمْ وَبَارِكْ عَلَى نَبِيِّنَا مُحَمَّدٍ ﷺ", W / 2, 1060, 50, GOLD2, k2, glow=1)
    es(c, "Oh Allah, bendice, da paz y prosperidad a nuestro Profeta Muhammad ﷺ", W / 2, 1150, 32, CRM, k2, 900)

# ------------------------------------------------------------ 8) medallón final
def medallion(c, x, y, R, T, a):
    g = cairo.RadialGradient(x, y, 0, x, y, R * 0.7)
    g.add_color_stop_rgba(0, 1, 0.97, 0.85, a); g.add_color_stop_rgba(0.3, *GOLD2, 0.6 * a); g.add_color_stop_rgba(1, *GOLD2, 0)
    c.new_path(); c.arc(x, y, R * 0.7, 0, 2 * math.pi); c.set_source(g); c.fill()
    for layer, (n, r, sp) in enumerate(((12, R * 0.92, 0.12), (8, R * 0.7, -0.18), (16, R * 0.5, 0.25))):
        c.save(); c.translate(x, y); c.rotate(T * sp)
        for i in range(n):
            c.rotate(2 * math.pi / n)
            c.new_path(); c.rectangle(-r * 0.6, -r * 0.6, r * 1.2, r * 1.2); c.set_line_width(2); c.set_source_rgba(*GOLD, 0.45 * a); c.stroke()
        c.restore()
    gold_ring(c, x, y, R, a, 3)

def sc_final(c, T):
    a = fade(T, 104.0, SPEECH_END, 1.0, 0.6)
    k = ease((T - 104.5) / 2.0)
    medallion(c, W / 2, 960, 300 * (0.3 + 0.7 * k), T, a * k)
    # una estrella que orbita
    ang = T * 1.2
    dot(c, W / 2 + math.cos(ang) * 330 * k, 960 + math.sin(ang) * 330 * k, 7, a * k, glow=1)
    k2 = fade(T, 106.5, SPEECH_END, 0.8, 0.6)
    ar(c, "ﷺ", W / 2, 1420, 120, GOLD2, k2, glow=1)
    es(c, "La paz y las bendiciones de Allah sean con él", W / 2, 1560, 38, CRM, k2, 900)

SCENES7 = [(0, 8.6, sc_orbit), (8.4, 35.0, sc_calls), (35.2, 44.0, sc_qul), (44.2, 59.0, sc_titles), (59.0, 73.0, sc_ayat),
           (73.0, 91.0, sc_adhan), (90.5, 104.0, sc_salawat), (104.0, SPEECH_END, sc_final)]

# ------------------------------------------------------------ marca y cierre
def logo_img(c, x, y, size, a=1.0, round_=True):
    c.save()
    if round_:
        c.new_path(); c.arc(x, y, size / 2, 0, 2 * math.pi); c.clip()
    sc = size / LOGO.get_width()
    c.translate(x - size / 2, y - size / 2); c.scale(sc, sc)
    c.set_source_surface(LOGO, 0, 0); c.get_source().set_filter(cairo.FILTER_BEST)
    c.paint_with_alpha(a); c.restore()

def watermark(c):
    circle(c, 112, 128, 72, GOLD, 0.95); circle(c, 112, 128, 67, (0, 0, 0))
    logo_img(c, 112, 128, 134, 1.0)
    font(c, 46, True); c.move_to(200, 145); c.set_source_rgba(*GOLD2, 0.95); c.show_text("Casa Antigua")

def end_card(c, t):
    k = ease(t / 0.8)
    c.set_source_rgb(0, 0, 0); c.paint()
    for i in range(12):
        a = i * math.pi / 6 + t * 0.2
        line(c, W / 2, 800, W / 2 + math.cos(a) * 900, 800 + math.sin(a) * 900, 60, GOLD, 0.05)
    with pop(c, W / 2, 800, t / 0.7):
        logo_img(c, W / 2, 800, 820, 1.0, round_=False)
    text_c(c, "Casa Antigua", W / 2, 1320 + (1 - k) * 40, 100, GOLD, k)
    k2 = ease((t - 0.8) / 0.6)
    rrect(c, W / 2 - 260, 1410, 520, 110, 55); fill(c, GOLD, k2)
    text_c(c, "Suscríbete", W / 2, 1484, 54, (0, 0, 0), k2)

def frame(c, t):
    if t >= SPEECH_END:
        end_card(c, t - SPEECH_END); return
    background(c, t, stars=clamp((t - 103.5) / 1.5))
    for s, e, fn in SCENES7:
        if s <= t < e: fn(c, t)
    watermark(c)

surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
ctx = cairo.Context(surf)
ctx.set_antialias(cairo.ANTIALIAS_BEST)
if PREVIEW is not None:
    frame(ctx, PREVIEW); surf.write_to_png(OUT); sys.exit()
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", SRC, "-map", "0:v", "-map", "1:a",
    "-af", f"atrim=0:{SPEECH_END},afade=t=out:st={SPEECH_END-1.0}:d=1.0,apad",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "160k", "-t", str(TOTAL), "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
nf = int(TOTAL * FPS)
for i in range(nf):
    frame(ctx, i / FPS); surf.flush()
    enc.stdin.write(bytes(surf.get_data()))
enc.stdin.close(); enc.wait(); print("frames", nf)
