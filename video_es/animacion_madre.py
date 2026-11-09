"""Animación flat vector «Servir a la madre» (1080x1920), subtítulos en español y marca de agua «Casa Antigua».

Uso: python3 animacion_flat.py <video_o_audio_original> <salida.mp4> [segundo_preview]
"""
import math, subprocess, sys
import cairo

SRC = sys.argv[1]
OUT = sys.argv[2]
PREVIEW = float(sys.argv[3]) if len(sys.argv) > 3 else None
W, H, FPS = 1080, 1920, 30
SPEECH_END = 71.9
END_CARD = 4.0
TOTAL = SPEECH_END + END_CARD

def hx(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) / 255 for i in (0, 2, 4))

BG = hx("F4EBDD"); PANEL = hx("FBF6EE"); NAVY = hx("1F3A4D"); TEAL = hx("2A7F7A")
TERRA = hx("C8603C"); SAND = hx("E3B964"); OLIVE = hx("7E8B4F"); CREAM = hx("FFFDF8")
SKY = hx("CFE3E0"); RED = hx("D2453A"); BROWN = hx("8A5A3B"); GREY = hx("B9B2A6")
SKIN = hx("D9A47E")

SUBS = [
(0.0,2.9,"Tu servicio a tu *madre*"),
(2.9,3.7,"es *obligatorio*."),
(3.7,6.4,"Es mejor que sentarte a leer el *Corán*."),
(6.4,8.1,"Tu servicio a tu *madre*,"),
(8.1,9.4,"cuidarla,"),
(9.4,12.1,"es mejor que la oración sunnah de *Duha*."),
(12.1,13.7,"Tu servicio a tu *madre*,"),
(13.7,15.1,"cuidarla,"),
(15.1,16.4,"es mejor que la *caridad*"),
(16.4,19.1,"que das en *caridad* a otros."),
(19.1,20.9,"La gente debe *saber* que"),
(20.9,22.6,"ser *bondadoso* con los padres,"),
(22.6,24.5,"obedecer a los padres y *servir* a los padres"),
(24.5,26.5,"están entre las *mayores* *obligaciones*"),
(26.5,29.3,"y entre los *mayores* *deberes*."),
(29.3,30.5,"La *prueba* de ello"),
(30.5,32.7,"son las palabras de *Allah* en el *Corán*,"),
(32.7,33.9,"donde menciona *Su* *derecho*"),
(33.9,35.5,"y después menciona el *derecho* *de* *los* *padres*."),
(35.5,36.3,"Él, el Altísimo, dijo:"),
(36.3,39.1,"«Adoren a *Allah* y no le asocien nada»"),
(39.1,40.8,"«y sean *bondadosos* con sus padres»."),
(40.8,43.5,"«Tu Señor ha decretado que no adoren sino a *Él*»"),
(43.5,45.7,"«y que sean *bondadosos* con los padres»."),
(45.7,47.0,"«Y le hemos *ordenado* al ser humano"),
(47.0,48.6,"ser *bondadoso* con sus padres»."),
(48.6,49.9,"«Y le hemos *ordenado* al ser humano"),
(49.9,51.6,"ser *bueno* con sus padres»."),
(51.6,54.7,"El *Profeta* (la paz sea con él) insistió y repitió"),
(54.7,60.1,"y explicó en detalle este asunto:"),
(60.1,62.1,"el de ser *bondadoso* con los padres."),
(62.1,64.3,"Un hombre vino a él queriendo hacer *yihad* por la causa de Allah."),
(64.3,65.5,"Él (la paz sea con él) dijo: «¿Viven tus *padres*?»"),
(65.5,66.3,"Respondió: «*Sí*»."),
(66.3,68.3,"Él (la paz sea con él) dijo: «Entonces *esfuérzate* en servirlos»."),
(68.3,69.8,"Toda persona que es *bondadosa* con sus padres,"),
(69.8,71.0,"esto es de las *mayores* formas de *yihad*"),
(71.0,SPEECH_END,"por la causa de *Allah*."),
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

SPEAKER = "Sheij Aziz bin Farhan al-Anizi"

# --- texto árabe (PIL + raqm para el ligado correcto) -> superficie cairo
import io
from PIL import Image as _PImage, ImageDraw as _PDraw, ImageFont as _PFont
_AR_FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes", "Amiri-Bold.ttf")

def arabic_surface(txt, size, col, maxw=820):
    f = _PFont.truetype(_AR_FONT, size, layout_engine=_PFont.Layout.RAQM)
    words = txt.split(); lines = [[]]
    for w in words:  # ajuste de línea (orden lógico; raqm resuelve la dirección)
        test = " ".join(lines[-1] + [w])
        if lines[-1] and f.getlength(test, direction="rtl") > maxw: lines.append([w])
        else: lines[-1].append(w)
    lines = [" ".join(l) for l in lines]
    lh = int(size * 1.75); wmax = int(max(f.getlength(l, direction="rtl") for l in lines)) + 40
    im = _PImage.new("RGBA", (wmax, lh * len(lines) + 30), (0, 0, 0, 0)); d = _PDraw.Draw(im)
    rgb = tuple(int(v * 255) for v in col)
    for i, l in enumerate(lines):
        lw = f.getlength(l, direction="rtl")
        d.text(((wmax - lw) / 2, 10 + i * lh), l, font=f, fill=rgb + (255,), direction="rtl", language="ar")
    buf = io.BytesIO(); im.save(buf, "PNG"); buf.seek(0)
    return cairo.ImageSurface.create_from_png(buf)

def blit(c, surf, x, y, a=1.0, scale=1.0):
    c.save(); c.translate(x, y); c.scale(scale, scale)
    c.set_source_surface(surf, -surf.get_width() / 2, -surf.get_height() / 2)
    c.get_source().set_filter(cairo.FILTER_BEST); c.paint_with_alpha(a); c.restore()

GOLD_ = hx("C9A060"); GREEN = hx("3E8E5E"); DKGREEN = hx("2F6B4A")
AYAT = [
    (36.3, 40.8, "Corán 4:36", "وَاعْبُدُوا اللَّهَ وَلَا تُشْرِكُوا بِهِ شَيْئًا ۖ وَبِالْوَالِدَيْنِ إِحْسَانًا"),
    (40.8, 45.7, "Corán 17:23", "وَقَضَىٰ رَبُّكَ أَلَّا تَعْبُدُوا إِلَّا إِيَّاهُ وَبِالْوَالِدَيْنِ إِحْسَانًا"),
    (45.7, 48.6, "Corán 29:8", "وَوَصَّيْنَا الْإِنسَانَ بِوَالِدَيْهِ حُسْنًا"),
    (48.6, 51.6, "Corán 46:15", "وَوَصَّيْنَا الْإِنسَانَ بِوَالِدَيْهِ إِحْسَانًا"),
]
AYAT_S = [arabic_surface(a[3], 64, NAVY) for a in AYAT]
HADITH_S = arabic_surface("فَفِيهِمَا فَجَاهِدْ", 76, NAVY)

# --- personajes
def mother(c, x, feet, h, dress=TEAL, scarf=SAND, arm=0.0):
    """Madre sin rostro con hiyab."""
    hr = h * 0.12
    c.save(); c.translate(x, feet)
    bw = h * 0.42
    c.new_path(); c.move_to(-bw / 2, 0); c.line_to(bw / 2, 0)
    c.curve_to(bw * 0.42, -h * 0.4, bw * 0.4, -h * 0.74, 0, -h * 0.76)
    c.curve_to(-bw * 0.4, -h * 0.74, -bw * 0.42, -h * 0.4, -bw / 2, 0); fill(c, dress)
    sy = -h * 0.62; L = h * 0.28
    ang = lerp(0.25, 1.3, arm)
    line(c, bw * 0.36, sy, bw * 0.36 + math.sin(ang) * L, sy + math.cos(ang) * L, h * 0.07, dress)
    line(c, -bw * 0.36, sy, -bw * 0.36 - h * 0.06, sy + L, h * 0.07, dress)
    hy = -h * 0.76 - hr * 0.9
    c.new_path(); c.move_to(-hr * 1.3, -h * 0.66); c.curve_to(-hr * 1.5, hy - hr * 1.4, hr * 1.5, hy - hr * 1.4, hr * 1.3, -h * 0.66); c.close_path(); fill(c, scarf)
    c.new_path(); c.save(); c.translate(0, hy + hr * 0.12); c.scale(0.78, 0.92); c.arc(0, 0, hr, 0, 2 * math.pi); c.restore(); fill(c, SKIN)
    c.restore()

def heart(c, x, y, s, col, a=1.0):
    c.new_path(); c.move_to(x, y + s * 0.9)
    c.curve_to(x - s * 1.4, y - s * 0.1, x - s * 0.7, y - s * 1.1, x, y - s * 0.45)
    c.curve_to(x + s * 0.7, y - s * 1.1, x + s * 1.4, y - s * 0.1, x, y + s * 0.9); c.close_path(); fill(c, col, a)

def floating_hearts(c, t, x, y, n=5, spread=220):
    for i in range(n):
        k = (t * 0.45 + i / n) % 1
        heart(c, x + math.sin(i * 2.3 + t) * spread * 0.5 + (i - n / 2) * spread / n, y - k * 260, 22 * (1 - k * 0.4), TERRA, math.sin(k * math.pi))

def tag(c, x, y, txt, bg, fg, size=34, a=1.0):
    font(c, size, True); w = c.text_extents(txt).x_advance + size * 1.4
    rrect(c, x - w / 2, y - size * 0.95, w, size * 1.7, size * 0.85); fill(c, bg, a)
    text_c(c, txt, x, y + size * 0.3, size, fg, a)

def badge_check(c, x, y, r, k):
    with pop(c, x, y, k):
        circle(c, x, y, r, GOLD_)
        c.new_path(); c.set_line_width(r * 0.22); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.move_to(x - r * 0.45, y + r * 0.02); c.line_to(x - r * 0.1, y + r * 0.38); c.line_to(x + r * 0.5, y - r * 0.35); c.set_source_rgb(*CREAM); c.stroke()

# --- escenas
def sc_mom(c, t, d):
    ground(c, SAND)
    mother(c, CX - 130, GROUND + 40, 560, TEAL, SAND, arm=0.15)
    person(c, CX + 140, GROUND + 40, 330, TERRA, point=0.0, wave=0.0)
    # el hijo le da la mano
    line(c, CX + 82, GROUND - 175, CX - 20, GROUND - 170, 24, TERRA)
    floating_hearts(c, t, CX, GROUND - 480, 5, 300)
    if t > 2.9:
        tag(c, CX, PY + 140, "Obligatorio", GOLD_, CREAM, 44, ease((t - 2.9) / 0.4))

def quran_book(c, x, y, s, col=TEAL):
    c.save(); c.translate(x, y); c.scale(s, s)
    line(c, -70, 40, 70, -10, 14, BROWN); line(c, 70, 40, -70, -10, 14, BROWN)  # atril
    for sd in (-1, 1):
        c.new_path(); c.move_to(0, 0); c.curve_to(sd * 40, -20, sd * 80, -18, sd * 110, -8)
        c.line_to(sd * 110, -90); c.curve_to(sd * 80, -100, sd * 40, -102, 0, -84); c.close_path(); fill(c, col)
        c.new_path(); c.move_to(0, -6); c.curve_to(sd * 40, -24, sd * 80, -22, sd * 100, -14)
        c.line_to(sd * 100, -86); c.curve_to(sd * 80, -94, sd * 40, -96, 0, -80); c.close_path(); fill(c, CREAM)
    c.restore()

def sun(c, x, y, r, t):
    for i in range(12):
        a = i * math.pi / 6 + t * 0.4
        line(c, x + math.cos(a) * r * 1.3, y + math.sin(a) * r * 1.3, x + math.cos(a) * r * 1.65, y + math.sin(a) * r * 1.65, r * 0.18, SAND)
    circle(c, x, y, r, SAND); circle(c, x, y, r * 0.7, hx("EFC977"))

def coins(c, x, y, s):
    for i in range(5):
        c.new_path(); c.save(); c.translate(x, y - i * 16 * s); c.scale(1, 0.35); c.arc(0, 0, 50 * s, 0, 2 * math.pi); c.restore(); fill(c, GOLD_)
        c.new_path(); c.save(); c.translate(x, y - i * 16 * s - 4 * s); c.scale(1, 0.3); c.arc(0, 0, 40 * s, 0, 2 * math.pi); c.restore(); fill(c, SAND)

def sc_balance(c, t, d):
    ground(c, SAND)
    T = t + 3.7  # tiempo absoluto
    items = [(3.7, "Leer el Corán"), (9.4, "Oración de Duha"), (15.1, "Caridad")]
    cur = max(i for i, (st, _) in enumerate(items) if T >= st)
    since = T - items[cur][0]
    wob = math.exp(-since * 3) * math.sin(since * 12) * 0.12
    tilt = -0.22 * ease(since / 0.9) - wob * 0
    tilt = -0.22 + wob
    px_, py_ = CX, PY + 330
    rrect(c, px_ - 18, py_, 36, GROUND - py_, 10); fill(c, BROWN)
    rrect(c, px_ - 140, GROUND - 20, 280, 40, 16); fill(c, BROWN)
    arm = 330
    lx, ly = px_ - math.cos(tilt) * arm, py_ - math.sin(tilt) * arm
    rx, ry = px_ + math.cos(tilt) * arm, py_ + math.sin(tilt) * arm
    line(c, lx, ly, rx, ry, 18, NAVY); circle(c, px_, py_, 24, GOLD_)
    for (x, y) in ((lx, ly), (rx, ry)):
        line(c, x, y, x - 100, y + 190, 4, NAVY); line(c, x, y, x + 100, y + 190, 4, NAVY)
        c.new_path(); c.move_to(x - 130, y + 190); c.line_to(x + 130, y + 190); c.curve_to(x + 100, y + 240, x - 100, y + 240, x - 130, y + 190); fill(c, NAVY)
    # corazón = servir a la madre (más pesado)
    pulse = 1 + 0.12 * max(0, math.sin(T * 6)) * (1 if (6.4 <= T < 9.4 or 12.1 <= T < 15.1) else 0.3)
    heart(c, lx, ly + 140, 62 * pulse, TERRA)
    tag(c, lx, ly + 300, "Servir a la madre", TERRA, CREAM, 30)
    k = since / 0.5
    with pop(c, rx, ry + 150, k):
        if cur == 0: quran_book(c, rx, ry + 185, 0.9)
        elif cur == 1: sun(c, rx, ry + 130, 50, T)
        else: coins(c, rx, ry + 175, 0.9)
    tag(c, rx, ry + 300, items[cur][1], CREAM, NAVY, 30, ease(k))
    # signo "mejor que"
    if since > 0.6:
        text_c(c, ">", CX, PY + 200, 120, GOLD_, ease((since - 0.6) / 0.4))

def father(c, x, feet, h, t=0.0):
    person(c, x, feet, h, NAVY, cap=CREAM)
    line(c, x + h * 0.26, feet - h * 0.45, x + h * 0.3, feet, h * 0.035, BROWN)
    line(c, x + h * 0.2, feet - h * 0.45, x + h * 0.27, feet - h * 0.45, h * 0.035, BROWN)

def tray_cup(c, x, y, t):
    rrect(c, x - 70, y, 140, 14, 7); fill(c, GOLD_)
    rrect(c, x - 26, y - 46, 52, 46, 10); fill(c, CREAM)
    for i in range(2):
        k = (t * 0.7 + i * 0.5) % 1
        c.new_path(); c.set_line_width(6); c.set_line_cap(cairo.LINE_CAP_ROUND)
        bx = x - 8 + i * 16
        c.move_to(bx, y - 56 - k * 60); c.curve_to(bx + 14, y - 70 - k * 60, bx - 14, y - 86 - k * 60, bx, y - 100 - k * 60)
        c.set_source_rgba(*GREY, 1 - k); c.stroke()

def sc_parents(c, t, d):
    ground(c, SAND)
    T = t + 19.1
    father(c, CX - 330, GROUND + 40, 560)
    mother(c, CX - 90, GROUND + 40, 520, TEAL, SAND)
    walk = ease(t / 2.0)
    kx = lerp(PX + PW + 100, CX + 230, walk)
    bob = abs(math.sin(t * 8)) * 8 * (1 - walk)
    person(c, kx, GROUND + 40 - bob, 380, TERRA, point=1.0)
    tray_cup(c, kx + 120, GROUND - 230 - bob, t)
    if T > 20.9: floating_hearts(c, T - 20.9, CX - 210, GROUND - 520, 4, 280)
    if T > 24.5:
        k = (T - 24.5) / 0.5
        with pop(c, CX + 280, PY + 170, k):
            for i in range(10):
                a = i * math.pi / 5 + T * 0.5
                line(c, CX + 280, PY + 170, CX + 280 + math.cos(a) * 120, PY + 170 + math.sin(a) * 120, 10, SAND, 0.6)
            circle(c, CX + 280, PY + 170, 78, GOLD_); star(c, CX + 280, PY + 172, 48, CREAM)
        text_c(c, "Gran deber", CX + 280, PY + 300, 36, NAVY, ease(k))

def sc_rights(c, t, d):
    T = t + 29.3
    for i in range(14):
        a = i * math.pi / 7 + t * 0.15
        c.new_path(); c.move_to(CX, PY + 480); c.line_to(CX + math.cos(a) * 900 - math.sin(a) * 60, PY + 480 + math.sin(a) * 900 + math.cos(a) * 60)
        c.line_to(CX + math.cos(a) * 900 + math.sin(a) * 60, PY + 480 + math.sin(a) * 900 - math.cos(a) * 60); c.close_path(); fill(c, SAND, 0.25)
    with pop(c, CX, PY + 470, t / 0.6):
        quran_book(c, CX, PY + 520, 2.2, DKGREEN)
    if T > 32.7:
        tag(c, CX, PY + 650, "Derecho de Allah", GOLD_, CREAM, 44, ease((T - 32.7) / 0.4))
    if T > 33.9:
        k = ease((T - 33.9) / 0.4)
        line(c, CX, PY + 700, CX, PY + 700 + 80 * k, 10, NAVY)
        c.new_path(); c.move_to(CX - 24, PY + 760 + 20 * k); c.line_to(CX + 24, PY + 760 + 20 * k); c.line_to(CX, PY + 790 + 20 * k); c.close_path(); fill(c, NAVY, k)
        tag(c, CX, PY + 870, "Derecho de los padres", NAVY, CREAM, 44, ease((T - 34.2) / 0.4))
    if T > 35.5:
        text_c(c, "Él, el Altísimo, dijo:", CX, PY + 140, 44, TEAL, ease((T - 35.5) / 0.4))

def arch_frame(c, x, top, w, h, col, inner):
    c.new_path(); c.move_to(x - w / 2, top + h); c.line_to(x - w / 2, top + w / 2)
    c.curve_to(x - w / 2, top + w * 0.15, x - w * 0.1, top + 30, x, top)
    c.curve_to(x + w * 0.1, top + 30, x + w / 2, top + w * 0.15, x + w / 2, top + w / 2)
    c.line_to(x + w / 2, top + h); c.close_path(); fill(c, col)
    m = 26
    c.new_path(); c.move_to(x - w / 2 + m, top + h - m); c.line_to(x - w / 2 + m, top + w / 2 + m * 0.4)
    c.curve_to(x - w / 2 + m, top + w * 0.15 + m, x - w * 0.1, top + 30 + m, x, top + m * 1.2)
    c.curve_to(x + w * 0.1, top + 30 + m, x + w / 2 - m, top + w * 0.15 + m, x + w / 2 - m, top + w / 2 + m * 0.4)
    c.line_to(x + w / 2 - m, top + h - m); c.close_path(); fill(c, inner)

def lantern(c, x, y, t, ph):
    sw = 0.12 * math.sin(t * 1.6 + ph)
    c.save(); c.translate(x, PY); c.rotate(sw)
    line(c, 0, 0, 0, y - PY, 4, NAVY)
    c.translate(0, y - PY)
    c.new_path(); c.move_to(-30, 0); c.line_to(30, 0); c.line_to(40, 50); c.line_to(0, 110); c.line_to(-40, 50); c.close_path(); fill(c, GOLD_)
    circle(c, 0, 50, 18, hx("FFE7A8")); c.restore()

def sc_ayah(c, t, d):
    T = t + 36.3
    lantern(c, PX + 120, PY + 150, T, 0); lantern(c, PX + PW - 120, PY + 200, T, 1.5)
    arch_frame(c, CX, PY + 90, 720, 800, DKGREEN, CREAM)
    for i, (s, e, ref, _) in enumerate(AYAT):
        if not (s <= T < e): continue
        k = ease((T - s) / 0.5) * (ease((e - T) / 0.3) if i < len(AYAT) - 1 else 1)
        tag(c, CX, PY + 330, ref, GOLD_, CREAM, 34, k)
        blit(c, AYAT_S[i], CX, PY + 580 + (1 - k) * 30, k, min(1.0, 600 / AYAT_S[i].get_width()))
    rrect(c, CX - 200, PY + 820, 400, 12, 6); fill(c, GOLD_)

def medina_mosque(c, x, base, t):
    c.new_path(); c.arc(x, base - 230, 150, math.pi, 2 * math.pi); fill(c, GREEN)
    rrect(c, x - 230, base - 230, 460, 230, 6); fill(c, CREAM)
    line(c, x, base - 380, x, base - 430, 8, GOLD_)
    c.new_path(); c.arc(x, base - 450, 18, 0.6, 2 * math.pi - 0.6); fill(c, GOLD_)
    for sx in (-1, 1):
        mx = x + sx * 320
        rrect(c, mx - 30, base - 520, 60, 520, 8); fill(c, CREAM)
        rrect(c, mx - 44, base - 380, 88, 22, 6); fill(c, GOLD_)
        c.new_path(); c.move_to(mx - 36, base - 520); c.line_to(mx + 36, base - 520); c.line_to(mx, base - 610); c.close_path(); fill(c, GREEN)
    for i in (-1, 0, 1):
        c.new_path(); ax = x + i * 120
        c.move_to(ax - 36, base); c.line_to(ax - 36, base - 100); c.arc(ax, base - 100, 36, math.pi, 2 * math.pi); c.line_to(ax + 36, base); c.close_path(); fill(c, DKGREEN)

def palm(c, x, base, s, t):
    c.new_path(); c.move_to(x - 12 * s, base); c.curve_to(x - 8 * s, base - 150 * s, x + 10 * s, base - 260 * s, x + 20 * s, base - 300 * s)
    c.line_to(x + 34 * s, base - 300 * s); c.curve_to(x + 22 * s, base - 250 * s, x + 12 * s, base - 150 * s, x + 12 * s, base); c.close_path(); fill(c, BROWN)
    tx, ty = x + 27 * s, base - 300 * s
    for i in range(7):
        a = -math.pi / 2 + (i - 3) * 0.55 + 0.05 * math.sin(t * 1.5 + i)
        c.new_path(); c.move_to(tx, ty)
        c.curve_to(tx + math.cos(a - 0.3) * 80 * s, ty + math.sin(a - 0.3) * 80 * s, tx + math.cos(a) * 150 * s, ty + math.sin(a) * 150 * s + 40 * s, tx + math.cos(a) * 170 * s, ty + math.sin(a) * 170 * s + 60 * s)
        c.curve_to(tx + math.cos(a) * 120 * s, ty + math.sin(a) * 120 * s + 20 * s, tx + math.cos(a + 0.3) * 60 * s, ty + math.sin(a + 0.3) * 60 * s, tx, ty)
        fill(c, OLIVE)

def scroll(c, x, y, w, k, t):
    h = 300 * k
    if h < 2: return
    rrect(c, x - w / 2, y, w, h, 10); fill(c, CREAM)
    for i in range(int(h / 50)):
        rrect(c, x - w / 2 + 50, y + 40 + i * 50, (w - 100) * (0.9 if i % 2 else 0.7), 12, 6); fill(c, GREY, 0.8)
    for yy in (y, y + h):
        rrect(c, x - w / 2 - 20, yy - 18, w + 40, 36, 18); fill(c, BROWN)

def sc_prophet(c, t, d):
    T = t + 51.6
    c.save(); rrect(c, PX, PY, PW, GROUND - PY, 0); c.clip()
    c.set_source_rgb(*hx("223B55")); c.paint(); c.restore()
    for i in range(18):
        k = (T * 0.4 + i * 0.37) % 1
        star(c, PX + 40 + (i * 157) % (PW - 80), PY + 60 + (i * 89) % 380, 10 * (0.4 + 0.6 * math.sin(k * math.pi)), CREAM, 0.9)
    c.new_path(); c.arc(PX + PW - 170, PY + 150, 70, 0, 2 * math.pi); c.arc_negative(PX + PW - 140, PY + 130, 62, 2 * math.pi, 0); fill(c, SAND)
    ground(c, SAND); rrect(c, PX, GROUND, PW, PY + PH - GROUND, 0); fill(c, hx("E9D3A8"))
    rise = ease(t / 1.2)
    medina_mosque(c, CX, GROUND + 10 + 80 * (1 - rise), T)
    palm(c, PX + 90, GROUND + 20, 1.3, T); palm(c, PX + PW - 110, GROUND + 20, 1.1, T)
    if T > 54.7:
        with pop(c, CX, PY + 200, (T - 54.7) / 0.5):
            tag(c, CX, PY + 130, "Hadiz", GOLD_, CREAM, 40)
            scroll(c, CX, PY + 180, 560, ease((T - 55.0) / 1.0), T)
    if T > 60.1:
        with pop(c, CX, PY + 330, (T - 60.1) / 0.5):
            circle(c, CX, PY + 330, 90, TERRA); heart(c, CX, PY + 330, 44, CREAM)

def masjid_door(c, x, base, w, h, col):
    c.new_path(); c.move_to(x - w / 2, base); c.line_to(x - w / 2, base - h + w / 2); c.arc(x, base - h + w / 2, w / 2, math.pi, 2 * math.pi); c.line_to(x + w / 2, base); c.close_path(); fill(c, col)

def traveler(c, x, feet, h, t, walking=0.0, wave=0.0):
    bob = abs(math.sin(t * 8)) * 8 * walking
    person(c, x, feet - bob, h, TEAL, cap=CREAM, wave=wave)
    rrect(c, x - h * 0.3, feet - bob - h * 0.66, h * 0.16, h * 0.3, 14); fill(c, BROWN)

def sc_jihad(c, t, d):
    T = t + 62.1
    rrect(c, PX, PY, PW, GROUND - PY, 0); fill(c, hx("F3E2C7"))
    masjid_door(c, CX - 230, GROUND + 4, 380, 700, CREAM)
    masjid_door(c, CX - 230, GROUND + 4, 300, 600, DKGREEN)
    # luz a la izquierda (no se representa al Profeta ﷺ)
    for i in range(6):
        circle(c, CX - 230, GROUND - 260, 60 + i * 30, hx("FFE7A8"), 0.12)
    ground(c, SAND)
    tag(c, CX, PY + 70, "Al-Bujari 3004 · Muslim 2549", NAVY, CREAM, 28)
    walk = ease(t / 1.6)
    traveler(c, lerp(PX + PW + 80, CX + 220, walk), GROUND + 40, 470, t, 1 - walk)
    if T > 64.3:
        with pop(c, CX - 120, PY + 240, (T - 64.3) / 0.4):
            bubble(c, CX - 120, PY + 240, 520, 110, "¿Viven tus padres?", GOLD_, CREAM, 44, tail=-1)
    if T > 65.5:
        with pop(c, CX + 260, PY + 420, (T - 65.5) / 0.4):
            bubble(c, CX + 260, PY + 420, 200, 100, "¡Sí!", TEAL, CREAM, 50, tail=1)

def house(c, x, base, s):
    c.new_path(); c.move_to(x - 210 * s, base - 260 * s); c.line_to(x, base - 420 * s); c.line_to(x + 210 * s, base - 260 * s); c.close_path(); fill(c, TERRA)
    rrect(c, x - 170 * s, base - 270 * s, 340 * s, 270 * s, 4); fill(c, SAND)
    c.new_path(); c.move_to(x - 45 * s, base); c.line_to(x - 45 * s, base - 120 * s); c.arc(x, base - 120 * s, 45 * s, math.pi, 2 * math.pi); c.line_to(x + 45 * s, base); c.close_path(); fill(c, NAVY)
    rrect(c, x - 140 * s, base - 210 * s, 60 * s, 60 * s, 8); fill(c, hx("FFE7A8"))
    rrect(c, x + 80 * s, base - 210 * s, 60 * s, 60 * s, 8); fill(c, hx("FFE7A8"))

def sc_return(c, t, d):
    T = t + 66.3
    rrect(c, PX, PY, PW, GROUND - PY, 0); fill(c, hx("F6DDB8"))
    sun(c, PX + 160, PY + 380, 60, T)
    with pop(c, CX, PY + 150, t / 0.5):
        rrect(c, CX - 300, PY + 80, 600, 150, 30); fill(c, CREAM)
        blit(c, HADITH_S, CX, PY + 150, 1.0, min(1.0, 520 / HADITH_S.get_width()))
    ground(c, SAND)
    house(c, CX + 250, GROUND + 10, 0.95)
    father(c, CX + 60, GROUND + 40, 420)
    mother(c, CX + 450, GROUND + 40, 390, TEAL, SAND)
    walk = ease(t / 2.2)
    traveler(c, lerp(PX - 60, CX - 200, walk), GROUND + 40, 440, t, 1 - walk, wave=ease((t - 2.2) / 0.5))
    if t > 2.0: floating_hearts(c, t - 2.0, CX - 60, GROUND - 450, 5, 300)
    if T > 69.8:
        k = (T - 69.8) / 0.5
        with pop(c, CX - 300, PY + 400, k):
            for i in range(10):
                a = i * math.pi / 5 + T * 0.6
                line(c, CX - 300, PY + 400, CX - 300 + math.cos(a) * 110, PY + 400 + math.sin(a) * 110, 9, GOLD_, 0.6)
            circle(c, CX - 300, PY + 400, 70, GOLD_); star(c, CX - 300, PY + 402, 42, CREAM)

def star(c, x, y, r, col, a=1.0):
    if r <= 0: return
    c.new_path()
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.42
        ang = -math.pi / 2 + i * math.pi / 5
        (c.move_to if i == 0 else c.line_to)(x + math.cos(ang) * rr, y + math.sin(ang) * rr)
    c.close_path(); fill(c, col, a)

SCENES = [
    (0.0, 3.7, sc_mom, PANEL), (3.7, 19.1, sc_balance, SKY), (19.1, 29.3, sc_parents, PANEL),
    (29.3, 36.3, sc_rights, hx("F6E2C4")), (36.3, 51.6, sc_ayah, SKY), (51.6, 62.1, sc_prophet, PANEL),
    (62.1, 66.3, sc_jihad, PANEL), (66.3, SPEECH_END, sc_return, PANEL),
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
