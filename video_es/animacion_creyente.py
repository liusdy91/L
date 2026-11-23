"""Animación flat vector «La condición del creyente» (1080x1920), subtítulos en español y marca de agua «Casa Antigua».

Uso: python3 animacion_flat.py <video_o_audio_original> <salida.mp4> [segundo_preview]
"""
import math, subprocess, sys
import cairo

SRC = sys.argv[1]
OUT = sys.argv[2]
PREVIEW = float(sys.argv[3]) if len(sys.argv) > 3 else None
W, H, FPS = 1080, 1920, 30
SPEECH_END = 32.5
END_CARD = 4.0
TOTAL = SPEECH_END + END_CARD

def hx(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) / 255 for i in (0, 2, 4))

BG = hx("F4EBDD"); PANEL = hx("FBF6EE"); NAVY = hx("1F3A4D"); TEAL = hx("2A7F7A")
TERRA = hx("C8603C"); SAND = hx("E3B964"); OLIVE = hx("7E8B4F"); CREAM = hx("FFFDF8")
SKY = hx("CFE3E0"); RED = hx("D2453A"); BROWN = hx("8A5A3B"); GREY = hx("B9B2A6")
SKIN = hx("D9A47E")

SUBS = [
(0.0,3.0,"Porque la naturaleza de esta vida es, en su origen, la *prueba*."),
(3.0,4.5,"Así que lo que estás viviendo…"),
(4.5,7.0,"es una *prueba* de Allah, Glorificado y Exaltado, para ti."),
(7.0,9.0,"Es la *vida* que Allah, Glorificado y Exaltado, *escribió* para ti."),
(9.0,10.5,"Así que estás *conforme* con lo que Allah decreta:"),
(10.5,12.5,"si es *bien*, pues bien;"),
(12.5,13.5,"y si es *mal*, pues mal."),
(13.5,17.0,"Te *sometes* a la orden de Allah, Glorificado y Exaltado."),
(17.0,20.0,"Y el creyente, si le llega algo *bueno*, *agradece*,"),
(20.0,20.5,"y eso es *bueno* para él;"),
(20.5,23.5,"y si le llega una *adversidad*, es *paciente*,"),
(23.5,25.5,"y eso es *bueno* para él."),
(25.5,27.5,"«Cuando recibe, *agradece*;"),
(27.5,29.0,"cuando es probado, es *paciente*;"),
(29.0,31.0,"y cuando peca, pide *perdón*»."),
(31.0,SPEECH_END,"Esta es la *condición* del *creyente*."),
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

SPEAKER = "La condición del creyente"

import io
from PIL import Image as _PImage, ImageDraw as _PDraw, ImageFont as _PFont
_AR_FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes", "Amiri-Bold.ttf")

def arabic_surface(txt, size, col, maxw=780):
    f = _PFont.truetype(_AR_FONT, size, layout_engine=_PFont.Layout.RAQM)
    words = txt.split(); lines = [[]]
    for w in words:
        test = " ".join(lines[-1] + [w])
        if lines[-1] and f.getlength(test, direction="rtl") > maxw: lines.append([w])
        else: lines[-1].append(w)
    lines = [" ".join(l) for l in lines]
    lh = int(size * 1.8); wmax = int(max(f.getlength(l, direction="rtl") for l in lines)) + 40
    im = _PImage.new("RGBA", (wmax, lh * len(lines) + 30), (0, 0, 0, 0)); d = _PDraw.Draw(im)
    rgb = tuple(int(v * 255) for v in col)
    for i, l in enumerate(lines):
        lw = f.getlength(l, direction="rtl")
        d.text(((wmax - lw) / 2, 10 + i * lh), l, font=f, fill=rgb + (255,), direction="rtl", language="ar")
    buf = io.BytesIO(); im.save(buf, "PNG"); buf.seek(0)
    return cairo.ImageSurface.create_from_png(buf)

def blit(c, surf, x, y, a=1.0, scale=1.0):
    if a <= 0: return
    c.save(); c.translate(x, y); c.scale(scale, scale)
    c.set_source_surface(surf, -surf.get_width() / 2, -surf.get_height() / 2)
    c.get_source().set_filter(cairo.FILTER_BEST); c.paint_with_alpha(a); c.restore()

GOLD_ = hx("C9A060"); GLOW = hx("FFE7A8"); DKGREEN = hx("2F6B4A"); WATER = hx("6FB7D6"); STORM = hx("5A6578")

AR = [
    (0.0, 3.0, "لِأَنَّ الدُّنْيَا طَبِيعَتُهَا الِابْتِلَاءُ أَصْلًا"),
    (3.0, 4.5, "فَقَدْ يَكُونُ مَا أَنْتَ فِيهِ.."),
    (4.5, 7.0, "هُوَ ابْتِلَاءٌ مِنَ اللهِ سُبْحَانَهُ وَتَعَالَى لَكَ"),
    (7.0, 9.0, "فَهُوَ الْحَيَاةُ الَّتِي كَتَبَهَا اللهُ سُبْحَانَهُ وَتَعَالَى لَكَ"),
    (9.0, 10.5, "فَأَنْتَ رَاضٍ بِمَا يَكْتُبُهُ اللهُ"),
    (10.5, 12.5, "إِنْ خَيْرًا.. فَخَيْرٌ"),
    (12.5, 13.5, "وَإِنْ شَرًّا.. فَشَرٌّ"),
    (13.5, 17.0, "فَأَنْتَ مُسْلِمٌ بِأَمْرِ اللهِ سُبْحَانَهُ وَتَعَالَى"),
    (17.0, 20.0, "وَالْمُؤْمِنُ إِذَا أَصَابَتْهُ سَرَّاءُ.. شَكَرَ"),
    (20.0, 20.5, "فَكَانَ خَيْرًا لَهُ"),
    (20.5, 23.5, "وَإِنْ أَصَابَتْهُ ضَرَّاءُ.. صَبَرَ"),
    (23.5, 25.5, "فَكَانَ خَيْرًا لَهُ"),
    (25.5, 27.5, "وَإِذَا أُعْطِيَ شَكَرَ"),
    (27.5, 29.0, "وَإِذَا ابْتُلِيَ صَبَرَ"),
    (29.0, 31.0, "وَإِذَا أَذْنَبَ اسْتَغْفَرَ"),
    (31.0, SPEECH_END, "هَذَا حَالُ الْمُؤْمِنِ"),
]
AR_S = [arabic_surface(x[2], 62, CREAM) for x in AR]

def arabic_card(c, T):
    for i, (s, e, _) in enumerate(AR):
        if not (s <= T < e): continue
        k = ease((T - s) / 0.35)
        rrect(c, CX - 440, PY + 40, 880, 150, 40); fill(c, NAVY, 0.85)
        sf = AR_S[i]; sc = min(1.0, 820 / sf.get_width(), 130 / sf.get_height())
        blit(c, sf, CX, PY + 115 + (1 - k) * 12, k, sc)

def tag(c, x, y, txt, bg, fg, size=34, a=1.0):
    if a <= 0: return
    font(c, size, True); w = c.text_extents(txt).x_advance + size * 1.4
    rrect(c, x - w / 2, y - size * 0.95, w, size * 1.7, size * 0.85); fill(c, bg, a)
    text_c(c, txt, x, y + size * 0.3, size, fg, a)

def check(c, x, y, r, k, col=TEAL):
    with pop(c, x, y, k):
        circle(c, x, y, r, col)
        c.new_path(); c.set_line_width(r * 0.22); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.move_to(x - r * 0.45, y + r * 0.02); c.line_to(x - r * 0.1, y + r * 0.38); c.line_to(x + r * 0.5, y - r * 0.35); c.set_source_rgb(*CREAM); c.stroke()

def star(c, x, y, r, col, a=1.0):
    if r <= 0: return
    c.new_path()
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.42
        ang = -math.pi / 2 + i * math.pi / 5
        (c.move_to if i == 0 else c.line_to)(x + math.cos(ang) * rr, y + math.sin(ang) * rr)
    c.close_path(); fill(c, col, a)

def sky(c, top, bottom):
    g = cairo.LinearGradient(0, PY, 0, GROUND)
    g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(1, *bottom)
    c.rectangle(PX, PY, PW, PH); c.set_source(g); c.fill()

def sun(c, x, y, r, t, a=1.0):
    for i in range(12):
        ang = i * math.pi / 6 + t * 0.4
        line(c, x + math.cos(ang) * r * 1.3, y + math.sin(ang) * r * 1.3, x + math.cos(ang) * r * 1.65, y + math.sin(ang) * r * 1.65, r * 0.18, SAND, a)
    circle(c, x, y, r, SAND, a); circle(c, x, y, r * 0.7, hx("EFC977"), a)

def cloud(c, x, y, s, col, a=1.0):
    for dx, dy, r in ((-80, 10, 60), (-20, -30, 80), (60, 0, 65), (110, 20, 45), (-130, 25, 40)):
        circle(c, x + dx * s, y + dy * s, r * s, col, a)
    rrect(c, x - 160 * s, y + 10 * s, 300 * s, 60 * s, 30 * s); fill(c, col, a)

def rain(c, x, y, w, h, t, a=1.0):
    for i in range(18):
        k = (t * 1.6 + i / 18) % 1
        xx = x + (i * 47) % w
        line(c, xx, y + k * h, xx - 8, y + k * h + 26, 4, WATER, a * (1 - k * 0.5))

def hands_up(c, x, feet, h, col, t):
    """Persona con las manos alzadas (gratitud / súplica)."""
    person(c, x, feet, h, col, cap=CREAM, wave=0.9 + 0.05 * math.sin(t * 3))

# ------------------------------------------------ escenas
def sc_test(c, t, d):
    T = t
    sky(c, hx("DCEEF2"), hx("F1F6F3")); ground(c, SAND)
    # camino con obstáculos: la vida es prueba
    c.new_path(); c.move_to(PX, GROUND + 60); c.curve_to(PX + 300, GROUND - 40, PX + 650, GROUND + 80, PX + PW, GROUND - 20)
    c.set_line_width(40); c.set_source_rgb(*hx("D8C3A0")); c.stroke()
    for i, x in enumerate((PX + 330, PX + 600, PX + 820)):
        with pop(c, x, GROUND + 10, (T - 0.6 - i * 0.4) / 0.4):
            rrect(c, x - 40, GROUND - 60, 80, 70, 14); fill(c, [BROWN, GREY, TERRA][i])
    u = clamp(T / 7.0)
    x = PX + 120 + u * 700; jump = abs(math.sin(u * math.pi * 4)) * 80
    person(c, x, GROUND + 40 - jump, 280, TEAL, cap=CREAM)
    tag(c, CX, PY + 280, "Esta vida es, por naturaleza, una prueba", DKGREEN, CREAM, 32, ease(T / 0.5))
    if T > 4.5: tag(c, CX, PY + 380, "Una prueba de Allah para ti", GOLD_, CREAM, 32, ease((T - 4.5) / 0.4))
    arabic_card(c, T)

def sc_written(c, t, d):
    T = t + 7.0
    sky(c, hx("F6E2C4"), hx("FBF1E0"))
    # pergamino que se escribe
    k = ease((T - 7.0) / 0.8)
    x0, y0, w, h = CX - 300, PY + 300, 600, 440 * k
    rrect(c, x0, y0, w, h, 12); fill(c, CREAM)
    for yy in (y0, y0 + h):
        rrect(c, x0 - 24, yy - 20, w + 48, 40, 20); fill(c, BROWN)
    n = int(clamp((T - 7.3) / 1.6) * 6)
    for i in range(n):
        rrect(c, x0 + 60, y0 + 60 + i * 60, (w - 120) * (0.9 if i % 2 else 0.7), 14, 7); fill(c, GREY)
    # pluma
    px_ = x0 + 60 + (w - 160) * ((T * 0.8) % 1); py_ = y0 + 60 + min(n, 5) * 60
    c.save(); c.translate(px_, py_); c.rotate(-0.6)
    c.new_path(); c.move_to(0, 0); c.curve_to(20, -60, 40, -140, 30, -200); c.curve_to(10, -140, -5, -60, 0, 0); fill(c, TEAL)
    c.restore()
    if T > 7.5: tag(c, CX, PY + 830, "La vida que Allah escribió para ti", NAVY, CREAM, 32, ease((T - 7.5) / 0.4))
    if T > 9.0:
        tag(c, CX, PY + 250, "Estás conforme", DKGREEN, CREAM, 34, ease((T - 9.0) / 0.4))
        check(c, x0 + w + 10, y0 - 10, 44, (T - 9.2) / 0.4)
    arabic_card(c, T)

def sc_good_bad(c, t, d):
    T = t + 10.5
    # mitad sol, mitad lluvia
    c.save(); c.rectangle(PX, PY, PW / 2, PH); c.clip(); sky(c, hx("FBE7B5"), hx("FDF3DC")); c.restore()
    c.save(); c.rectangle(CX, PY, PW / 2, PH); c.clip(); sky(c, hx("B9C3D0"), hx("DDE3EA")); c.restore()
    ground(c, SAND)
    k1 = (T - 10.5) / 0.5
    with pop(c, CX - 240, PY + 420, k1): sun(c, CX - 240, PY + 420, 80, T)
    tag(c, CX - 240, PY + 620, "Si es bien…", GOLD_, CREAM, 34, ease(k1))
    if T > 12.5:
        k2 = (T - 12.5) / 0.5
        with pop(c, CX + 240, PY + 400, k2):
            cloud(c, CX + 240, PY + 400, 1.0, STORM)
        rain(c, CX + 120, PY + 470, 260, 300, T, ease(k2))
        tag(c, CX + 240, PY + 620, "…o si es mal", STORM, CREAM, 34, ease(k2))
    person(c, CX, GROUND + 50, 300, TEAL, cap=CREAM)
    arabic_card(c, T)

def sc_submit(c, t, d):
    T = t + 13.5
    sky(c, hx("E9E3F0"), hx("F6F0EA")); ground(c, OLIVE)
    for i in range(12):
        a = i * math.pi / 6 + T * 0.2
        line(c, CX, PY + 440, CX + math.cos(a) * 340, PY + 440 + math.sin(a) * 340, 18, GLOW, 0.45 * ease((T - 13.5) / 0.8))
    person(c, CX, GROUND + 50, 400, TEAL, cap=CREAM, point=0.6)
    tag(c, CX, PY + 300, "Te sometes a la orden de Allah", DKGREEN, CREAM, 34, ease((T - 13.8) / 0.4))
    arabic_card(c, T)

def sc_believer(c, t, d):
    T = t + 17.0
    sky(c, hx("CFE3E0"), hx("EAF3EE")); ground(c, SAND)
    tag(c, CX, PY + 260, "El creyente", NAVY, CREAM, 38, ease((T - 17.0) / 0.4))
    # izquierda: alegría → gratitud
    with pop(c, CX - 240, PY + 400, (T - 17.2) / 0.5): sun(c, CX - 240, PY + 400, 60, T)
    hands_up(c, CX - 240, GROUND + 40, 300, TEAL, T)
    tag(c, CX - 240, GROUND + 100, "Agradece", GOLD_, CREAM, 32, ease((T - 18.0) / 0.4))
    if T > 20.0: check(c, CX - 90, PY + 360, 36, (T - 20.0) / 0.3)
    # derecha: adversidad → paciencia
    if T > 20.5:
        k = (T - 20.5) / 0.5
        with pop(c, CX + 240, PY + 390, k): cloud(c, CX + 240, PY + 390, 0.8, STORM)
        rain(c, CX + 140, PY + 450, 200, 250, T, ease(k))
        # paraguas: paciencia
        c.new_path(); c.arc(CX + 240, GROUND - 300, 120, math.pi, 2 * math.pi); fill(c, TERRA, ease(k))
        line(c, CX + 240, GROUND - 300, CX + 240, GROUND - 170, 8, BROWN, ease(k))
        person(c, CX + 240, GROUND + 40, 280, TEAL, cap=CREAM)
        tag(c, CX + 240, GROUND + 100, "Es paciente", TERRA, CREAM, 32, ease((T - 21.0) / 0.4))
    if T > 23.5:
        check(c, CX + 390, PY + 360, 36, (T - 23.5) / 0.3)
        tag(c, CX, PY + 560, "Y fue bueno para él", DKGREEN, CREAM, 36, ease((T - 23.5) / 0.4))
    arabic_card(c, T)

ICONS = [(25.5, "Si recibe", "agradece", GOLD_), (27.5, "Si es probado", "tiene paciencia", TERRA), (29.0, "Si peca", "pide perdón", TEAL)]
def icon(c, i, x, y, T):
    if i == 0:
        rrect(c, x - 50, y - 30, 100, 80, 10); fill(c, CREAM); rrect(c, x - 60, y - 50, 120, 26, 8); fill(c, CREAM)
        line(c, x, y - 50, x, y + 50, 14, GOLD_)
    elif i == 1:
        c.new_path(); c.arc(x, y + 10, 60, math.pi, 2 * math.pi); fill(c, CREAM); line(c, x, y + 10, x, y + 60, 8, CREAM)
    else:
        circle(c, x, y, 50, CREAM)
        for j in range(3):
            kk = (T * 0.8 + j / 3) % 1
            circle(c, x - 20 + j * 20, y - 60 - kk * 60, 8, CREAM, 1 - kk)
        c.new_path(); c.set_line_width(10); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(x - 22, y); c.line_to(x - 6, y + 18); c.line_to(x + 24, y - 16); c.set_source_rgb(*TEAL); c.stroke()

def sc_three(c, t, d):
    T = t + 25.5
    sky(c, hx("F3E6D2"), hx("FBF6EE"))
    for i, (st, a, b, col) in enumerate(ICONS):
        if T < st: continue
        y = PY + 330 + i * 200
        k = ease((T - st) / 0.4)
        with pop(c, CX, y, (T - st) / 0.4):
            rrect(c, PX + 70, y - 80, PW - 140, 160, 40); fill(c, col)
            circle(c, PX + 180, y, 64, NAVY, 0.25)
            icon(c, i, PX + 180, y, T)
            font(c, 34, False); c.move_to(PX + 290, y - 10); c.set_source_rgb(*CREAM); c.show_text(a)
            font(c, 48, True); c.move_to(PX + 290, y + 48); c.set_source_rgb(*CREAM); c.show_text(b)
    arabic_card(c, T)

def sc_condition(c, t, d):
    T = t + 31.0
    sky(c, hx("223B55"), hx("35557A"))
    for i in range(16):
        kk = (T * 0.4 + i * 0.37) % 1
        star(c, PX + 40 + (i * 157) % (PW - 80), PY + 260 + (i * 89) % 400, 9 * (0.4 + 0.6 * math.sin(kk * math.pi)), CREAM, 0.9)
    with pop(c, CX, CY + 60, (T - 31.0) / 0.5):
        for i in range(12):
            a = i * math.pi / 6 + T * 0.4
            line(c, CX, CY + 60, CX + math.cos(a) * 200, CY + 60 + math.sin(a) * 200, 14, GLOW, 0.5)
        circle(c, CX, CY + 60, 130, GOLD_); star(c, CX, CY + 62, 80, CREAM)
    tag(c, CX, PY + PH - 80, "Así es el creyente", GOLD_, CREAM, 40, ease((T - 31.2) / 0.4))
    arabic_card(c, T)

SCENES = [
    (0.0, 7.0, sc_test, PANEL), (7.0, 10.5, sc_written, PANEL), (10.5, 13.5, sc_good_bad, PANEL),
    (13.5, 17.0, sc_submit, PANEL), (17.0, 25.5, sc_believer, PANEL), (25.5, 31.0, sc_three, PANEL),
    (31.0, SPEECH_END, sc_condition, PANEL),
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
