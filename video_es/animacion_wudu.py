"""Animación flat vector «Los adhkar del wudu» (1080x1920), subtítulos en español y marca de agua «Casa Antigua».

Uso: python3 animacion_flat.py <video_o_audio_original> <salida.mp4> [segundo_preview]
"""
import math, subprocess, sys
import cairo

SRC = sys.argv[1]
OUT = sys.argv[2]
PREVIEW = float(sys.argv[3]) if len(sys.argv) > 3 else None
W, H, FPS = 1080, 1920, 30
SPEECH_END = 42.9
END_CARD = 4.0
TOTAL = SPEECH_END + END_CARD

def hx(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) / 255 for i in (0, 2, 4))

BG = hx("F4EBDD"); PANEL = hx("FBF6EE"); NAVY = hx("1F3A4D"); TEAL = hx("2A7F7A")
TERRA = hx("C8603C"); SAND = hx("E3B964"); OLIVE = hx("7E8B4F"); CREAM = hx("FFFDF8")
SKY = hx("CFE3E0"); RED = hx("D2453A"); BROWN = hx("8A5A3B"); GREY = hx("B9B2A6")
SKIN = hx("D9A47E")

SUBS = [
(0.0,3.5,"Memoriza de mí solo *tres* *adhkar* en el wudu'."),
(3.5,5.0,"No hay un *cuarto*."),
(5.0,6.5,"La *tasmiya* al inicio del wudu':"),
(6.5,7.5,"es decir «*Bismillah*» (en el nombre de Allah),"),
(7.5,9.0,"no la *basmala* completa."),
(9.0,10.0,"Algunas personas,"),
(10.0,10.5,"cuando van a hacer el wudu', dicen:"),
(10.5,11.5,"«En el nombre de Allah, el *Compasivo*, el *Misericordioso*»."),
(11.5,13.0,"No, esa es para la *oración*."),
(13.0,16.0,"En el wudu' dices: «*Bismillah*»."),
(16.0,19.0,"Durante el wudu' *no* *hay* *ninguna* *súplica*."),
(19.0,21.0,"No hay ninguna súplica durante el wudu'."),
(21.0,22.5,"*Después* del wudu',"),
(22.5,23.5,"dices estas *dos* súplicas,"),
(23.5,28.0,"y son por *alternancia*, no para *juntarlas*."),
(28.0,29.5,"O bien dices:"),
(29.5,30.5,"«Atestiguo que no hay dios digno de adoración salvo *Allah*,"),
(30.5,32.0,"*Único*, sin asociado,"),
(32.0,33.5,"y atestiguo que *Muhammad* es Su siervo y mensajero."),
(33.5,34.5,"Oh Allah, ponme entre los que se *arrepienten* mucho"),
(34.5,35.0,"y ponme entre los que se *purifican*»."),
(35.0,37.0,"Esta súplica la dices *a* *veces*."),
(37.0,38.0,"O dices la *segunda* súplica:"),
(38.0,39.5,"«*Glorificado* seas, oh Allah, y alabado;"),
(39.5,40.5,"atestiguo que no hay dios digno de adoración salvo *Tú*;"),
(40.5,42.0,"te pido *perdón* y me *arrepiento* ante Ti»."),
(42.0,SPEECH_END,"Esto es para *beneficio*."),
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

SPEAKER = "Los adhkar del wudu'"

import io
from PIL import Image as _PImage, ImageDraw as _PDraw, ImageFont as _PFont
_AR_FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes", "Amiri-Bold.ttf")

def arabic_surface(txt, size, col, maxw=760):
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

GOLD_ = hx("C9A060"); GLOW = hx("FFE7A8"); DKGREEN = hx("2F6B4A"); WATER = hx("6FB7D6")

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

def cross(c, x, y, r, k):
    with pop(c, x, y, k):
        circle(c, x, y, r, RED)
        line(c, x - r * 0.4, y - r * 0.4, x + r * 0.4, y + r * 0.4, r * 0.22, CREAM)
        line(c, x - r * 0.4, y + r * 0.4, x + r * 0.4, y - r * 0.4, r * 0.22, CREAM)

def drop(c, x, y, s, col=WATER, a=1.0):
    c.new_path(); c.move_to(x, y - 30 * s); c.curve_to(x + 22 * s, y - 2 * s, x + 22 * s, y + 18 * s, x, y + 18 * s)
    c.curve_to(x - 22 * s, y + 18 * s, x - 22 * s, y - 2 * s, x, y - 30 * s); fill(c, col, a)

def ewer(c, x, y, s, tilt=0.0):
    c.save(); c.translate(x, y); c.rotate(tilt); c.scale(s, s)
    c.new_path(); c.move_to(-60, 80); c.curve_to(-110, 20, -80, -60, -30, -70); c.line_to(30, -70)
    c.curve_to(80, -60, 110, 20, 60, 80); c.close_path(); fill(c, GOLD_)
    rrect(c, -40, -100, 80, 34, 10); fill(c, BROWN)
    c.new_path(); c.move_to(70, -10); c.curve_to(130, -30, 150, -80, 170, -100); c.line_to(180, -88)
    c.curve_to(160, -60, 140, -10, 80, 20); c.close_path(); fill(c, GOLD_)
    c.new_path(); c.arc(-95, 0, 40, math.pi * 0.6, math.pi * 1.4); c.set_line_width(14); c.set_source_rgb(*BROWN); c.stroke()
    c.restore()

def sky(c, top, bottom):
    g = cairo.LinearGradient(0, PY, 0, GROUND)
    g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(1, *bottom)
    c.rectangle(PX, PY, PW, PH); c.set_source(g); c.fill()

BISM = arabic_surface("بِسْمِ اللهِ", 110, NAVY)
BISM_FULL = arabic_surface("بِسْمِ اللهِ الرَّحْمَٰنِ الرَّحِيمِ", 64, GREY)
DUA1 = arabic_surface("أَشْهَدُ أَنْ لَا إِلَٰهَ إِلَّا اللهُ وَحْدَهُ لَا شَرِيكَ لَهُ، وَأَشْهَدُ أَنَّ مُحَمَّدًا عَبْدُهُ وَرَسُولُهُ، اللَّهُمَّ اجْعَلْنِي مِنَ التَّوَّابِينَ وَاجْعَلْنِي مِنَ الْمُتَطَهِّرِينَ", 54, NAVY, 780)
DUA2 = arabic_surface("سُبْحَانَكَ اللَّهُمَّ وَبِحَمْدِكَ، أَشْهَدُ أَنْ لَا إِلَٰهَ إِلَّا أَنْتَ، أَسْتَغْفِرُكَ وَأَتُوبُ إِلَيْكَ", 58, NAVY, 780)

# ------------------------------------------------ escenas
def sc_three(c, t, d):
    T = t
    sky(c, hx("DCEEF2"), hx("F1F6F3"))
    tag(c, CX, PY + 110, "Solo 3 adhkar en el wudu'", DKGREEN, CREAM, 40, ease(T / 0.4))
    labels = [("1", "Al inicio"), ("2", "Después · A"), ("3", "Después · B")]
    for i, (n, lab) in enumerate(labels):
        x = CX - 300 + i * 300
        with pop(c, x, CY, (T - 0.5 - i * 0.4) / 0.4):
            circle(c, x, CY - 20, 110, [TEAL, GOLD_, TERRA][i])
            text_c(c, n, x, CY + 20, 110, CREAM)
            tag(c, x, CY + 160, lab, NAVY, CREAM, 28)
    if T > 3.6:
        k = (T - 3.6) / 0.4
        with pop(c, CX, PY + PH - 190, k):
            circle(c, CX, PY + PH - 190, 80, GREY, 0.5)
            text_c(c, "4", CX, PY + PH - 160, 90, CREAM)
        cross(c, CX + 70, PY + PH - 250, 36, (T - 3.9) / 0.3)
        tag(c, CX, PY + PH - 60, "No hay un cuarto", RED, CREAM, 32, ease(k))

def sc_tasmiyah(c, t, d):
    T = t + 5.0
    sky(c, hx("F6E2C4"), hx("FBF1E0"))
    tag(c, CX, PY + 100, "Al inicio del wudu'", DKGREEN, CREAM, 38, ease((T - 5.0) / 0.4))
    # tarjeta correcta
    k1 = (T - 6.3) / 0.5
    with pop(c, CX, PY + 330, k1):
        rrect(c, CX - 330, PY + 200, 660, 260, 36); fill(c, CREAM)
        blit(c, BISM, CX, PY + 310, 1)
        text_c(c, "«En el nombre de Allah»", CX, PY + 420, 34, TEAL)
    if T > 7.0: check(c, CX + 310, PY + 210, 44, (T - 7.0) / 0.4)
    # la basmala completa: no
    if T > 7.5:
        k2 = ease((T - 7.5) / 0.5)
        rrect(c, CX - 380, PY + 530, 760, 230, 36); fill(c, hx("EDE6DA"), k2)
        blit(c, BISM_FULL, CX, PY + 610, k2)
        text_c(c, "«…el Compasivo, el Misericordioso»", CX, PY + 700, 30, GREY, k2)
        if T > 8.0: cross(c, CX + 360, PY + 540, 44, (T - 8.0) / 0.4)
    if T > 11.5:
        tag(c, CX, PY + 840, "Esa es para la oración", TERRA, CREAM, 36, ease((T - 11.5) / 0.4))
    elif T > 9.0:
        tag(c, CX, PY + 840, "Algunos dicen esto al hacer wudu'", GREY, NAVY, 30, ease((T - 9.0) / 0.4))

def sc_during(c, t, d):
    T = t + 16.0
    sky(c, hx("DCEEF2"), hx("EEF6F8")); ground(c, hx("CFE0E4"))
    tag(c, CX, PY + 100, "Durante el wudu'", DKGREEN, CREAM, 38, ease((T - 16.0) / 0.4))
    # jarra vertiendo agua sobre las manos
    ewer(c, CX - 170, PY + 380, 1.2, 0.35 + 0.05 * math.sin(T * 2))
    for i in range(10):
        k = (T * 1.4 + i / 10) % 1
        drop(c, CX + 60 + 14 * math.sin(i), PY + 330 + k * 430, 0.6, WATER, 1 - k * 0.6)
    for sx in (-1, 1):
        c.new_path(); c.save(); c.translate(CX + 60 + sx * 46, GROUND - 120); c.rotate(sx * 0.5); c.scale(0.7, 1.2); c.arc(0, 0, 50, 0, 2 * math.pi); c.restore(); fill(c, SKIN)
    # bocadillo de súplica tachado
    if T > 16.6:
        k = (T - 16.6) / 0.4
        with pop(c, CX + 260, PY + 330, k):
            bubble(c, CX + 260, PY + 330, 300, 110, "«Oh Allah…»", CREAM, NAVY, 38, tail=-1)
        if T > 17.2:
            kk = ease((T - 17.2) / 0.3)
            line(c, CX + 110, PY + 280, CX + 110 + 300 * kk, PY + 380, 14, RED)
        tag(c, CX, PY + PH - 70, "Ninguna súplica", RED, CREAM, 38, ease((T - 17.4) / 0.4))

def sc_after(c, t, d):
    T = t + 21.0
    sky(c, hx("F6E2C4"), hx("FBF1E0"))
    tag(c, CX, PY + 100, "Después del wudu'", DKGREEN, CREAM, 38, ease((T - 21.0) / 0.4))
    for i, (lab, col) in enumerate((("Súplica A", GOLD_), ("Súplica B", TERRA))):
        x = CX - 220 + i * 440
        with pop(c, x, CY - 60, (T - 22.3 - i * 0.3) / 0.4):
            rrect(c, x - 170, CY - 200, 340, 280, 30); fill(c, col)
            text_c(c, lab, x, CY - 50, 46, CREAM)
    if T > 23.5:
        k = ease((T - 23.5) / 0.5)
        # alternar: una u otra
        u = (math.sin((T - 23.5) * 2.2) + 1) / 2
        for i in range(2):
            x = CX - 220 + i * 440
            a = (1 - u) if i == 0 else u
            circle(c, x, CY + 140, 22, TEAL, k * (0.25 + 0.75 * a))
        tag(c, CX, CY + 250, "Alternándolas: una u otra", TEAL, CREAM, 36, k)
        line(c, CX - 120, CY + 380, CX + 120, CY + 380, 6, NAVY, k)
        text_c(c, "A + B juntas", CX, CY + 370, 36, NAVY, k)
        cross(c, CX + 200, CY + 355, 30, (T - 24.0) / 0.4)

def dua_card(c, T, s, surf, lab, lines_es, ref_k):
    k = ease((T - s) / 0.5)
    tag(c, CX, PY + 100, lab, GOLD_, CREAM, 38, k)
    rrect(c, PX + 40, PY + 170, PW - 80, 460, 36); fill(c, CREAM, k)
    sc = min(1.0, 820 / surf.get_width(), 420 / surf.get_height())
    blit(c, surf, CX, PY + 400, k, sc)
    for i, (st, txt) in enumerate(lines_es):
        if T < st: continue
        kk = ease((T - st) / 0.4)
        font(c, 30, True)
        rrect(c, PX + 70, PY + 670 + i * 72, PW - 140, 60, 20); fill(c, hx("E9F1EE"), kk)
        text_c(c, txt, CX, PY + 710 + i * 72, 30 if len(txt) < 46 else 26, NAVY, kk)

def sc_dua1(c, t, d):
    T = t + 28.0
    sky(c, hx("CFE3E0"), hx("EAF3EE"))
    dua_card(c, T, 28.0, DUA1, "Súplica A", [
        (29.5, "Atestiguo que no hay dios sino Allah, Único, sin asociado,"),
        (32.0, "y atestiguo que Muhammad es Su siervo y mensajero."),
        (33.5, "Oh Allah, ponme entre los que se arrepienten mucho"),
        (34.5, "y ponme entre los que se purifican."),
    ], 1)
    if T > 35.0: tag(c, CX, PY + PH - 40, "Esta la dices a veces", TEAL, CREAM, 32, ease((T - 35.0) / 0.4))

def sc_dua2(c, t, d):
    T = t + 37.0
    sky(c, hx("F3E6D2"), hx("FBF6EE"))
    dua_card(c, T, 37.0, DUA2, "Súplica B", [
        (38.0, "Glorificado seas, oh Allah, y alabado;"),
        (39.5, "atestiguo que no hay dios sino Tú;"),
        (40.5, "Te pido perdón y me arrepiento ante Ti."),
    ], 1)
    if T > 42.0: tag(c, CX, PY + PH - 40, "Para beneficio", DKGREEN, CREAM, 34, ease((T - 42.0) / 0.4))

SCENES = [
    (0.0, 5.0, sc_three, PANEL), (5.0, 16.0, sc_tasmiyah, PANEL), (16.0, 21.0, sc_during, PANEL),
    (21.0, 28.0, sc_after, PANEL), (28.0, 37.0, sc_dua1, PANEL), (37.0, SPEECH_END, sc_dua2, PANEL),
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
