"""Animación flat vector «Elige bien a tus amigos» (1080x1920), subtítulos en español y marca de agua «Casa Antigua».

Uso: python3 animacion_flat.py <video_o_audio_original> <salida.mp4> [segundo_preview]
"""
import math, subprocess, sys
import cairo

SRC = sys.argv[1]
OUT = sys.argv[2]
PREVIEW = float(sys.argv[3]) if len(sys.argv) > 3 else None
W, H, FPS = 1080, 1920, 30
SPEECH_END = 16.4
END_CARD = 4.0
TOTAL = SPEECH_END + END_CARD

def hx(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) / 255 for i in (0, 2, 4))

BG = hx("F4EBDD"); PANEL = hx("FBF6EE"); NAVY = hx("1F3A4D"); TEAL = hx("2A7F7A")
TERRA = hx("C8603C"); SAND = hx("E3B964"); OLIVE = hx("7E8B4F"); CREAM = hx("FFFDF8")
SKY = hx("CFE3E0"); RED = hx("D2453A"); BROWN = hx("8A5A3B"); GREY = hx("B9B2A6")
SKIN = hx("D9A47E")

SUBS = [
(0.2,3.0,"La persona debe *elegir* bien"),
(3.0,4.2,"a su *compañero*,"),
(4.2,6.0,"y elegir bien a su *amigo*."),
(6.0,7.1,"El *creyente* no debe"),
(7.1,9.0,"andar con *cualquiera*."),
(9.0,10.1,"Como dijo *al-Hasan*:"),
(10.1,11.0,"«El *creyente* no debe"),
(11.0,12.8,"andar con *cualquiera*;"),
(12.8,14.4,"no anda con todo el que *pasa*."),
(14.4,15.1,"*No*,"),
(15.1,SPEECH_END,"él *elige*»."),
]

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

import os
LOGO = cairo.ImageSurface.create_from_png(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_casa_antigua.png"))
GOLD = hx("C9A060")

def logo_img(c, x, y, size, a=1.0, round_=True):
    """Dibuja el logo real de Casa Antigua centrado en (x, y)."""
    c.save()
    if round_:
        c.new_path(); c.arc(x, y, size / 2, 0, 2 * math.pi); c.clip()
    sc = size / LOGO.get_width()
    c.translate(x - size / 2, y - size / 2); c.scale(sc, sc)
    c.set_source_surface(LOGO, 0, 0); c.get_source().set_filter(cairo.FILTER_BEST)
    c.paint_with_alpha(a); c.restore()

def watermark(c):
    circle(c, 112, 128, 72, GOLD, 0.95)
    circle(c, 112, 128, 67, (0, 0, 0))
    logo_img(c, 112, 128, 134, 1.0)
    font(c, 46, True); c.move_to(200, 145); c.set_source_rgba(*NAVY, 0.9); c.show_text("Casa Antigua")

def header(c, t):
    a = ease(t / 0.8)
    text_c(c, SPEAKER, W / 2, 285, 38, TEAL, a)
    rrect(c, 120, 318, W - 240, 10, 5); fill(c, NAVY, 0.1)
    rrect(c, 120, 318, (W - 240) * clamp(t / SPEECH_END), 10, 5); fill(c, TERRA)

def layout_sub(c, text, size, maxw):
    font(c, size, True); sp = c.text_extents(" ").x_advance
    toks = [(w.replace("*", ""), "*" in w) for w in text.split()]
    lines = [[]]; cw = 0
    for tk in toks:
        w = c.text_extents(tk[0]).x_advance
        if lines[-1] and cw + sp + w > maxw: lines.append([]); cw = 0
        cw += (sp if lines[-1] else 0) + w; lines[-1].append((tk[0], tk[1], w))
    return lines, sp

SUB_TOP, SUB_BOT = 1430, 1800
def subtitle(c, t):
    for s, e, txt in SUBS:
        if not (s <= t < e): continue
        size = 56
        lines, sp = layout_sub(c, txt, size, 940)
        if len(lines) > 4:
            size = 48; lines, sp = layout_sub(c, txt, size, 960)
        lh = size * 1.3
        top = SUB_TOP + (SUB_BOT - SUB_TOP - len(lines) * lh) / 2
        n = sum(len(l) for l in lines); span = min((e - s) * 0.55, 0.11 * n + 0.2)
        out = ease((e - t) / 0.18) if e - t < 0.18 else 1
        idx = 0
        for li, ln in enumerate(lines):
            lw = sum(w for _, _, w in ln) + sp * (len(ln) - 1)
            x = (W - lw) / 2
            for word, hl, w in ln:
                st = s + span * idx / max(1, n); idx += 1
                k = (t - st) / 0.28
                if k > 0:
                    cx, cy = x + w / 2, top + li * lh + size * 0.75
                    sc = 0.6 + 0.4 * back(k)
                    c.save(); c.translate(cx, cy + (1 - ease(k)) * 18); c.scale(sc, sc)
                    font(c, size, True); c.move_to(-w / 2, size * 0.35 - size * 0.37)
                    c.set_source_rgba(*(TERRA if hl else NAVY), ease(k) * out); c.show_text(word); c.restore()
                x += w + sp

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

# ---------------------------------------------------------------- render
def frame(c, t):
    if t >= SPEECH_END:
        end_card(c, t - SPEECH_END); watermark_on = False
        return
    c.set_source_rgb(*BG); c.paint()
    # puntos decorativos de fondo
    for i in range(14):
        x = (i * 173 + t * 8) % (W + 100) - 50; y = 1860 + (i * 37) % 40 + 6 * math.sin(t + i)
        circle(c, x, y, 6, SAND, 0.5)
    rrect(c, PX + 10, PY + 14, PW, PH, 48); fill(c, NAVY, 0.08)
    for s, e, fn, bg in SCENES:
        if not (s <= t < e): continue
        lt = t - s; d = e - s
        rrect(c, PX, PY, PW, PH, 48); fill(c, bg)
        c.save(); rrect(c, PX, PY, PW, PH, 48); c.clip()
        c.push_group()
        fn(c, lt, d)
        c.pop_group_to_source()
        fade = min(ease(lt / 0.35), ease((e - t) / 0.25) if e < SPEECH_END else 1)
        c.paint_with_alpha(fade); c.restore()
        # transición: barrido circular al entrar
        if lt < 0.45:
            c.save(); rrect(c, PX, PY, PW, PH, 48); c.clip()
            r = 1200 * ease(lt / 0.45)
            c.new_path(); c.rectangle(PX, PY, PW, PH); c.arc_negative(CX, CY, r, 2 * math.pi, 0)
            c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); fill(c, TERRA, 0.9 * (1 - ease(lt / 0.45)))
            c.set_fill_rule(cairo.FILL_RULE_WINDING); c.restore()
    header(c, t)
    subtitle(c, t)
    watermark(c)

SPEAKER = "Sheij Abdur-Razzaq al-Badr"

import io, random
from PIL import Image as _PImage, ImageDraw as _PDraw, ImageFont as _PFont
_AR_FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes", "Amiri-Bold.ttf")

def arabic_surface(txt, size, col):
    f = _PFont.truetype(_AR_FONT, size, layout_engine=_PFont.Layout.RAQM)
    lw = int(f.getlength(txt, direction="rtl")) + 40
    im = _PImage.new("RGBA", (lw, int(size * 1.9)), (0, 0, 0, 0)); d = _PDraw.Draw(im)
    d.text((20, 10), txt, font=f, fill=tuple(int(v * 255) for v in col) + (255,), direction="rtl", language="ar")
    buf = io.BytesIO(); im.save(buf, "PNG"); buf.seek(0)
    return cairo.ImageSurface.create_from_png(buf)

def blit(c, surf, x, y, a=1.0, scale=1.0):
    c.save(); c.translate(x, y); c.scale(scale, scale)
    c.set_source_surface(surf, -surf.get_width() / 2, -surf.get_height() / 2)
    c.get_source().set_filter(cairo.FILTER_BEST); c.paint_with_alpha(a); c.restore()

GOLD_ = hx("C9A060"); GLOW = hx("FFE7A8"); DUSK1 = hx("F2B97C"); DUSK2 = hx("F7DDB8")
AR = [
    (0.2, 3.0, "عَلَى الْإِنْسَانِ أَنْ يَتَخَيَّرَ"),
    (3.0, 4.2, "الرَّفِيقَ"),
    (4.2, 6.0, "وَيَتَخَيَّرَ الصَّاحِبَ"),
    (6.0, 7.1, "لَيْسَ لِلْمُؤْمِنِ"),
    (7.1, 9.0, "أَنْ يَمْشِيَ مَعَ مَنْ شَاءَ"),
    (9.0, 10.1, "كَمَا قَالَ الْحَسَنُ"),
    (10.1, 11.0, "لَيْسَ لِلْمُؤْمِنِ"),
    (11.0, 12.8, "أَنْ يَمْشِيَ مَعَ مَنْ شَاءَ"),
    (12.8, 14.4, "لَا يَمْشِي مَعَ كُلِّ مَنْ هَبَّ وَدَبَّ"),
    (14.4, 15.1, "لَا"),
    (15.1, SPEECH_END, "يَتَخَيَّرُ"),
]
AR_S = [arabic_surface(x[2], 70, CREAM) for x in AR]

def arabic_card(c, T):
    for i, (s, e, _) in enumerate(AR):
        if not (s <= T < e): continue
        k = ease((T - s) / 0.35)
        rrect(c, CX - 420, PY + 50, 840, 140, 40); fill(c, NAVY, 0.55)
        surf = AR_S[i]; sc = min(1.0, 780 / surf.get_width())
        blit(c, surf, CX, PY + 120 + (1 - k) * 14, k, sc)

def star(c, x, y, r, col, a=1.0):
    if r <= 0: return
    c.new_path()
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.42
        ang = -math.pi / 2 + i * math.pi / 5
        (c.move_to if i == 0 else c.line_to)(x + math.cos(ang) * rr, y + math.sin(ang) * rr)
    c.close_path(); fill(c, col, a)

def dusk(c, t):
    g = cairo.LinearGradient(0, PY, 0, GROUND)
    g.add_color_stop_rgb(0, *hx("E7A37A")); g.add_color_stop_rgb(0.6, *DUSK1); g.add_color_stop_rgb(1, *DUSK2)
    c.rectangle(PX, PY, PW, PH); c.set_source(g); c.fill()
    circle(c, CX + 260, GROUND - 120, 110, hx("FBD38D")); circle(c, CX + 260, GROUND - 120, 80, hx("FDE3AE"))
    circle(c, PX + 160, PY + 290, 46, CREAM, 0.85)
    for j, (yy, col) in enumerate(((GROUND - 60, hx("B5715A")), (GROUND - 20, hx("8E5A4A")))):
        c.new_path(); c.move_to(PX, yy)
        for i in range(7):
            c.curve_to(PX + i * 160 + 50, yy - 70 + j * 20, PX + i * 160 + 110, yy - 70 + j * 20, PX + (i + 1) * 160, yy)
        c.line_to(PX + PW, PY + PH); c.line_to(PX, PY + PH); c.close_path(); fill(c, col)
    rrect(c, PX, GROUND, PW, PY + PH - GROUND, 0); fill(c, hx("6E4A3E"))

def walker(c, x, feet, h, col, t, walking=1.0, cap=None, ph=0.0, **kw):
    bob = abs(math.sin(t * 7 + ph)) * 8 * walking
    person(c, x, feet - bob, h, col, cap=cap, **kw)

def spotlight(c, x, top, base, w, a):
    g = cairo.LinearGradient(0, top, 0, base)
    g.add_color_stop_rgba(0, *GLOW, 0.8 * a); g.add_color_stop_rgba(1, *GLOW, 0.1 * a)
    c.new_path(); c.move_to(x - 30, top); c.line_to(x + 30, top); c.line_to(x + w / 2, base); c.line_to(x - w / 2, base); c.close_path()
    c.set_source(g); c.fill()

def check(c, x, y, r, k):
    with pop(c, x, y, k):
        circle(c, x, y, r, TEAL)
        c.new_path(); c.set_line_width(r * 0.22); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.move_to(x - r * 0.45, y + r * 0.02); c.line_to(x - r * 0.1, y + r * 0.38); c.line_to(x + r * 0.5, y - r * 0.35); c.set_source_rgb(*CREAM); c.stroke()

def cross(c, x, y, r, k):
    with pop(c, x, y, k):
        circle(c, x, y, r, RED)
        line(c, x - r * 0.4, y - r * 0.4, x + r * 0.4, y + r * 0.4, r * 0.22, CREAM)
        line(c, x - r * 0.4, y + r * 0.4, x + r * 0.4, y - r * 0.4, r * 0.22, CREAM)

# --- escenas
CAND = [(-330, hx("8C8C8C")), (-110, hx("9A8F84")), (110, TEAL), (330, hx("8A8A96"))]

def sc_choose(c, t, d):
    T = t
    dusk(c, T)
    # el protagonista observa de espaldas al centro-abajo; los candidatos en fila
    sweep = ease_io(clamp((t - 0.6) / 2.4))
    sx = lerp(CX - 330, CX + 110, sweep) + math.sin(t * 3) * 40 * (1 - sweep)
    spotlight(c, sx, PY + 230, GROUND + 60, 260, ease(t / 0.6))
    for dx, col in CAND:
        hl = dx == 110 and t > 3.0
        walker(c, CX + dx, GROUND + 50, 380 if not hl else 400, col if (hl or t < 3.0) else tuple(v * 0.75 + 0.2 for v in col), t, 0, cap=CREAM if hl else None, ph=dx)
    if t > 3.0:
        check(c, CX + 110, PY + 340, 46, (t - 3.0) / 0.4)
    arabic_card(c, T)

def sc_together(c, t, d):
    T = t + 4.2
    dusk(c, T)
    # caminan juntos hacia el sol
    x = lerp(CX - 120, CX + 40, ease(t / 1.8))
    walker(c, x - 90, GROUND + 50, 400, NAVY, t, 1, cap=CREAM)
    walker(c, x + 90, GROUND + 50, 400, TEAL, t, 1, cap=CREAM, ph=1.2)
    line(c, x - 40, GROUND - 165, x + 40, GROUND - 165, 22, SKIN)  # de la mano
    for i in range(4):
        k = (t * 0.6 + i / 4) % 1
        heart_(c, x + (i - 1.5) * 60, GROUND - 450 - k * 160, 20, TERRA, math.sin(k * math.pi))
    arabic_card(c, T)

def heart_(c, x, y, s, col, a=1.0):
    c.new_path(); c.move_to(x, y + s * 0.9)
    c.curve_to(x - s * 1.4, y - s * 0.1, x - s * 0.7, y - s * 1.1, x, y - s * 0.45)
    c.curve_to(x + s * 0.7, y - s * 1.1, x + s * 1.4, y - s * 0.1, x, y + s * 0.9); c.close_path(); fill(c, col, a)

_rng = random.Random(7)
CROWD = [(_rng.uniform(0, 1), _rng.choice([-1, 1]), _rng.uniform(0.6, 1.2), _rng.choice([hx("8C8C8C"), hx("9A8F84"), hx("7D7A88"), hx("A08976")]), _rng.uniform(0, 1)) for _ in range(9)]

def crowd(c, t, speed=1.0, depth=True):
    for i, (x0, dr, sp, col, ph) in enumerate(sorted(CROWD, key=lambda z: z[4])):
        u = (x0 + dr * t * 0.09 * sp * speed) % 1
        x = PX - 80 + u * (PW + 160)
        sc = 0.75 + 0.35 * ph if depth else 1
        walker(c, x, GROUND + 20 + ph * 60, 300 * sc, col, t * sp, 1, ph=i)

def sc_crowd(c, t, d, T0=6.0):
    T = t + T0
    dusk(c, T)
    crowd(c, T)
    # el creyente se detiene, con la mano en alto (no se va con cualquiera)
    rrect(c, CX - 150, GROUND + 70, 300, 30, 15); fill(c, NAVY, 0.25)
    person(c, CX, GROUND + 90, 430, TEAL, cap=CREAM, point=ease((t - 0.5) / 0.5))
    if t > 1.0:
        cross(c, CX + 250, PY + 330, 50, (t - 1.0) / 0.4)
    arabic_card(c, T)

def sc_quote(c, t, d):
    T = t + 9.0
    dusk(c, T)
    with pop(c, CX, CY + 40, t / 0.4):
        rrect(c, CX - 330, CY - 200, 660, 420, 30); fill(c, CREAM)
        text_c(c, "“", CX - 250, CY - 40, 220, GOLD_)
        text_c(c, "Al-Hasan", CX + 30, CY + 30, 80, NAVY)
        text_c(c, "(al-Basri)", CX + 30, CY + 110, 46, TEAL, bold=False)
        rrect(c, CX - 200, CY + 160, 400, 10, 5); fill(c, GOLD_)
    arabic_card(c, T)

def sc_passers(c, t, d):
    T = t + 10.1
    dusk(c, T)
    crowd(c, T, speed=1.0 + 1.5 * ease((T - 12.8) / 0.6))
    rrect(c, CX - 150, GROUND + 70, 300, 30, 15); fill(c, NAVY, 0.25)
    person(c, CX, GROUND + 90, 430, TEAL, cap=CREAM, point=1.0)
    cross(c, CX + 250, PY + 330, 50, (t - 0.3) / 0.4)
    arabic_card(c, T)

def sc_chosen(c, t, d):
    T = t + 14.4
    dusk(c, T)
    if T < 15.1:
        k = ease(t / 0.3)
        with pop(c, CX, CY, t / 0.3):
            c.new_path()
            for i in range(8):
                a = math.pi / 8 + i * math.pi / 4
                (c.move_to if i == 0 else c.line_to)(CX + math.cos(a) * 200, CY + math.sin(a) * 200)
            c.close_path(); fill(c, RED)
            text_c(c, "NO", CX, CY + 50, 140, CREAM)
    else:
        u = T - 15.1
        spotlight(c, CX, PY + 230, GROUND + 60, 520, ease(u / 0.4))
        walker(c, CX - 90, GROUND + 50, 400, NAVY, u, 0, cap=CREAM)
        walker(c, CX + 90, GROUND + 50, 400, TEAL, u, 0, cap=CREAM)
        line(c, CX - 40, GROUND - 165, CX + 40, GROUND - 165, 22, SKIN)
        check(c, CX, PY + 330, 56, u / 0.4)
    arabic_card(c, T)

SCENES = [
    (0.0, 4.2, sc_choose, PANEL), (4.2, 6.0, sc_together, PANEL), (6.0, 9.0, sc_crowd, PANEL),
    (9.0, 10.1, sc_quote, PANEL), (10.1, 14.4, sc_passers, PANEL), (14.4, SPEECH_END, sc_chosen, PANEL),
]

surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
ctx = cairo.Context(surf)
ctx.set_antialias(cairo.ANTIALIAS_BEST)

if PREVIEW is not None:
    frame(ctx, PREVIEW); surf.write_to_png(OUT); sys.exit()

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", SRC, "-map", "0:v", "-map", "1:a",
    "-af", f"atrim=0:{SPEECH_END},afade=t=out:st={SPEECH_END-0.6}:d=0.6,apad",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "160k", "-t", str(TOTAL), "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
nf = int(TOTAL * FPS)
for i in range(nf):
    frame(ctx, i / FPS); surf.flush()
    enc.stdin.write(bytes(surf.get_data()))
enc.stdin.close(); enc.wait(); print("frames", nf)
