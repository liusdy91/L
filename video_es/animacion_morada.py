"""Animación flat vector «Esta vida es morada de paso» (1080x1920), subtítulos en español y marca de agua «Casa Antigua».

Uso: python3 animacion_flat.py <video_o_audio_original> <salida.mp4> [segundo_preview]
"""
import math, subprocess, sys
import cairo

SRC = sys.argv[1]
OUT = sys.argv[2]
PREVIEW = float(sys.argv[3]) if len(sys.argv) > 3 else None
W, H, FPS = 1080, 1920, 30
SPEECH_END = 78.6
END_CARD = 4.0
TOTAL = SPEECH_END + END_CARD

def hx(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) / 255 for i in (0, 2, 4))

BG = hx("F4EBDD"); PANEL = hx("FBF6EE"); NAVY = hx("1F3A4D"); TEAL = hx("2A7F7A")
TERRA = hx("C8603C"); SAND = hx("E3B964"); OLIVE = hx("7E8B4F"); CREAM = hx("FFFDF8")
SKY = hx("CFE3E0"); RED = hx("D2453A"); BROWN = hx("8A5A3B"); GREY = hx("B9B2A6")
SKIN = hx("D9A47E")

SUBS = [
(0.0,1.2,"Oh hermanos en Allah:"),
(1.2,2.8,"esta morada es morada de *obras*,"),
(2.8,4.1,"morada de *consejo* sincero,"),
(4.1,7.3,"morada de cooperar en la *bondad* y la *piedad*."),
(7.3,9.4,"No es morada de *deleite*,"),
(9.4,11.9,"ni morada de *eternidad*,"),
(11.9,13.0,"sino morada *pasajera*."),
(13.0,15.8,"Tú estás *de* *paso*."),
(15.8,18.0,"Sea larga o corta tu vida, estás *de* *paso*."),
(18.0,19.5,"No es tu *morada*;"),
(19.5,21.4,"te diriges a la *otra* *morada*:"),
(21.4,23.2,"o al *Paraíso* o al *Fuego*."),
(23.2,25.4,"Ante ti hay *rendición* *de* *cuentas* y retribución,"),
(25.4,27.3,"y *Paraíso* y *Fuego*,"),
(27.3,29.2,"y *libros* que se reparten:"),
(29.2,31.0,"uno toma su libro con la *derecha*"),
(31.0,33.5,"y otro toma su libro con la *izquierda*."),
(33.5,34.1,"Y hay una *balanza*:"),
(34.1,35.3,"a uno le *pesa* su balanza"),
(35.3,37.1,"y a otro se le *aligera*."),
(37.1,39.5,"«En cuanto a aquel cuyas obras *pesen* en la balanza,"),
(39.5,40.7,"tendrá una vida *placentera*."),
(40.7,42.5,"Y en cuanto a aquel cuyas obras pesen *poco*,"),
(42.5,44.2,"su morada será el *abismo*.»"),
(44.2,46.1,"«Quien reciba su libro en la *derecha*"),
(46.1,48.0,"será juzgado con un juicio *fácil*"),
(48.0,49.7,"y volverá con los suyos *alegre*.»"),
(49.7,52.1,"«Y quien reciba su libro en la *izquierda* dirá: ¡Ojalá no me hubieran dado mi libro!»"),
(52.1,53.9,"Lo importante es que *Allah*, Glorificado y Exaltado,"),
(53.9,55.6,"nos ha *advertido*"),
(55.6,56.9,"de este *momento*"),
(56.9,58.0,"y de este *encuentro*,"),
(58.0,60.6,"y nos lo ha *recordado*."),
(60.6,62.3,"Estás en *peligro*:"),
(62.3,64.6,"puede que recibas tu libro con la *izquierda*,"),
(64.6,66.4,"puede que tu balanza sea *ligera*."),
(66.4,67.6,"¡*Cuidado*, siervo de Allah!"),
(67.6,69.5,"*Prepárate* en esta morada,"),
(69.5,70.7,"*examina* tu alma,"),
(70.7,72.3,"¡*lucha* contra ella!"),
(72.3,74.9,"Reflexiona sobre lo que *salva* y practícalo,"),
(74.9,77.2,"y reflexiona sobre lo que *destruye* y cuídate de ello."),
(77.2,SPEECH_END,"Así es el *creyente*."),
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

SPEAKER = "Sheij Abdul-Aziz ibn Baz (rahimahullah)"

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

GOLD_ = hx("C9A060"); GLOW = hx("FFE7A8"); GREEN = hx("3E8E5E"); DKGREEN = hx("2F6B4A"); FIRE = hx("E4572E"); FIRE2 = hx("F3A33A")

def star(c, x, y, r, col, a=1.0):
    if r <= 0: return
    c.new_path()
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.42
        ang = -math.pi / 2 + i * math.pi / 5
        (c.move_to if i == 0 else c.line_to)(x + math.cos(ang) * rr, y + math.sin(ang) * rr)
    c.close_path(); fill(c, col, a)

def tag(c, x, y, txt, bg, fg, size=34, a=1.0):
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

def walker(c, x, feet, h, col, t, walking=1.0, cap=CREAM, ph=0.0, **kw):
    bob = abs(math.sin(t * 7 + ph)) * 8 * walking
    person(c, x, feet - bob, h, col, cap=cap, **kw)

def book(c, x, y, s, col, ang=0.0):
    c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s)
    rrect(c, -50, -65, 100, 130, 10); fill(c, col)
    rrect(c, -38, -65, 88, 120, 6); fill(c, CREAM)
    rrect(c, -50, -65, 22, 130, 6); fill(c, col)
    for i in range(4): rrect(c, -18, -40 + i * 24, 54, 8, 4); fill(c, GREY)
    c.restore()

def scale_(c, t, tilt, cx, py_, base, lcol=GREEN, rcol=RED, litems=None, ritems=None):
    rrect(c, cx - 18, py_, 36, base - py_, 10); fill(c, BROWN)
    rrect(c, cx - 140, base - 20, 280, 40, 16); fill(c, BROWN)
    arm = 320
    lx, ly = cx - math.cos(tilt) * arm, py_ + math.sin(tilt) * arm
    rx, ry = cx + math.cos(tilt) * arm, py_ - math.sin(tilt) * arm
    line(c, lx, ly, rx, ry, 18, NAVY); circle(c, cx, py_, 24, GOLD_)
    for (x, y, col) in ((lx, ly, lcol), (rx, ry, rcol)):
        line(c, x, y, x - 100, y + 190, 4, NAVY); line(c, x, y, x + 100, y + 190, 4, NAVY)
        c.new_path(); c.move_to(x - 130, y + 190); c.line_to(x + 130, y + 190); c.curve_to(x + 100, y + 240, x - 100, y + 240, x - 130, y + 190); fill(c, col)
    return (lx, ly), (rx, ry)

def flame(c, x, base, h, t, ph=0.0):
    w = h * 0.45; f = math.sin(t * 9 + ph) * h * 0.06
    c.new_path(); c.move_to(x - w, base); c.curve_to(x - w * 1.1, base - h * 0.5, x - w * 0.2 + f, base - h * 0.7, x + f, base - h)
    c.curve_to(x + w * 0.4 + f, base - h * 0.6, x + w * 1.1, base - h * 0.45, x + w, base); c.close_path(); fill(c, FIRE)
    c.new_path(); c.move_to(x - w * 0.5, base); c.curve_to(x - w * 0.6, base - h * 0.3, x - w * 0.1 - f, base - h * 0.45, x - f * 0.5, base - h * 0.6)
    c.curve_to(x + w * 0.3, base - h * 0.35, x + w * 0.6, base - h * 0.25, x + w * 0.5, base); c.close_path(); fill(c, FIRE2)

def sky(c, top, bottom):
    g = cairo.LinearGradient(0, PY, 0, GROUND)
    g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(1, *bottom)
    c.rectangle(PX, PY, PW, PH); c.set_source(g); c.fill()

# ------------------------------------------------ escenas
def sc_work(c, t, d):
    """Esta vida: morada de obras, consejo y cooperación."""
    sky(c, hx("BFE0DC"), hx("EAF3EE"))
    ground(c, OLIVE)
    # dos personas llevan juntas una caja (cooperación)
    x = lerp(CX - 380, CX - 80, ease(t / 3.0))
    walker(c, x - 120, GROUND + 40, 380, NAVY, t, 1 - ease(t / 3.0))
    walker(c, x + 120, GROUND + 40, 380, TEAL, t, 1 - ease(t / 3.0), ph=1)
    rrect(c, x - 90, GROUND - 230, 180, 110, 12); fill(c, SAND)
    line(c, x - 90, GROUND - 175, x + 90, GROUND - 175, 6, BROWN, 0.5)
    # planta que crece (obras)
    g = ease((t - 0.5) / 5)
    px_ = CX + 300
    rrect(c, px_ - 60, GROUND - 40, 120, 80, 12); fill(c, TERRA)
    line(c, px_, GROUND - 40, px_, GROUND - 40 - 260 * g, 14, OLIVE)
    for i in range(int(g * 5)):
        s = 1 if i % 2 else -1; yy = GROUND - 90 - i * 45
        c.save(); c.translate(px_, yy); c.rotate(s * 0.6)
        c.new_path(); c.move_to(0, 0); c.curve_to(s * 30, -40, s * 90, -30, s * 100, 0); c.curve_to(s * 70, 25, s * 30, 25, 0, 0); fill(c, TEAL); c.restore()
    T = t
    if T > 1.2: tag(c, CX, PY + 120, "Morada de obras", GOLD_, CREAM, 40, ease((T - 1.2) / 0.4))
    if T > 2.8: tag(c, CX - 200, PY + 230, "Consejo", TEAL, CREAM, 32, ease((T - 2.8) / 0.4))
    if T > 4.1: tag(c, CX + 170, PY + 230, "Bondad y piedad", TERRA, CREAM, 32, ease((T - 4.1) / 0.4))

def hourglass(c, x, y, s, k, t):
    c.save(); c.translate(x, y); c.scale(s, s)
    rrect(c, -130, -230, 260, 30, 12); fill(c, BROWN); rrect(c, -130, 200, 260, 30, 12); fill(c, BROWN)
    line(c, -110, -200, -110, 200, 14, BROWN); line(c, 110, -200, 110, 200, 14, BROWN)
    c.new_path(); c.move_to(-90, -200); c.line_to(90, -200); c.curve_to(90, -80, 12, -30, 12, 0); c.curve_to(12, 30, 90, 80, 90, 200)
    c.line_to(-90, 200); c.curve_to(-90, 80, -12, 30, -12, 0); c.curve_to(-12, -30, -90, -80, -90, -200); c.close_path(); fill(c, CREAM, 0.85)
    top = 1 - k
    if top > 0.02:
        c.new_path(); h = 170 * top
        c.move_to(-80 * top ** 0.5, -30 - h + 30 * 0); c.line_to(80 * top ** 0.5, -30 - h); c.line_to(12, -20); c.line_to(-12, -20); c.close_path(); fill(c, SAND)
        line(c, 0, -10, 0, 190, 5, SAND)
    c.new_path(); hb = 160 * k + 8
    c.move_to(-88, 198); c.line_to(88, 198); c.curve_to(60, 198 - hb, 20, 198 - hb * 1.1, 0, 198 - hb * 1.15); c.curve_to(-20, 198 - hb * 1.1, -60, 198 - hb, -88, 198); c.close_path(); fill(c, SAND)
    c.restore()

def sc_passing(c, t, d):
    T = t + 7.3
    sky(c, hx("F3D9B1"), hx("F8E8CF"))
    ground(c, SAND)
    hourglass(c, CX, CY + 10, 1.25, clamp(t / d), t)
    # flores que se marchitan (no es morada de deleite ni eternidad)
    wil = ease((t - 1.0) / 3.0)
    for i, fx in enumerate((CX - 330, CX + 330)):
        line(c, fx, GROUND + 20, fx + 50 * wil * (1 if i else -1), GROUND - 200 + 60 * wil, 10, OLIVE)
        cx_, cy_ = fx + 60 * wil * (1 if i else -1), GROUND - 210 + 90 * wil
        for j in range(5):
            circle(c, cx_ + math.cos(j * 1.26) * 30, cy_ + math.sin(j * 1.26) * 30, 22 * (1 - 0.5 * wil), TERRA if i else SAND, 1 - 0.6 * wil)
        circle(c, cx_, cy_, 16, BROWN)
    if T > 11.9: tag(c, CX, PY + 110, "Morada pasajera", NAVY, CREAM, 40, ease((T - 11.9) / 0.4))

def gate(c, x, base, w, h, col, inner, a=1.0):
    c.new_path(); c.move_to(x - w / 2, base); c.line_to(x - w / 2, base - h + w / 2); c.arc(x, base - h + w / 2, w / 2, math.pi, 2 * math.pi); c.line_to(x + w / 2, base); c.close_path(); fill(c, col, a)
    m = 22
    c.new_path(); c.move_to(x - w / 2 + m, base); c.line_to(x - w / 2 + m, base - h + w / 2); c.arc(x, base - h + w / 2, w / 2 - m, math.pi, 2 * math.pi); c.line_to(x + w / 2 - m, base); c.close_path(); fill(c, inner, a)

def sc_moving(c, t, d):
    T = t + 13.0
    # el sol cruza el cielo (vida larga o corta)
    sky(c, hx("CFE3E0"), hx("F3E6D2"))
    u = clamp(t / d)
    sx = lerp(PX + 120, PX + PW - 120, u); sy = PY + 420 - math.sin(u * math.pi) * 230
    circle(c, sx, sy, 60, SAND)
    # camino en perspectiva
    c.new_path(); ground(c, OLIVE)
    c.new_path(); c.move_to(CX - 60, GROUND - 120); c.line_to(CX + 60, GROUND - 120); c.line_to(CX + 380, PY + PH); c.line_to(CX - 380, PY + PH); c.close_path(); fill(c, hx("D8C3A0"))
    for i in range(6):
        k = ((i / 6) + t * 0.25) % 1
        yy = GROUND - 120 + k * (PY + PH - GROUND + 120); ww = 6 + k * 18
        rrect(c, CX - ww / 2, yy, ww, 20 + k * 30, 4); fill(c, CREAM, 0.8)
    # puerta lejana: la otra morada
    ga = ease((T - 19.5) / 0.8)
    gate(c, CX, GROUND - 118, 150, 230, GOLD_, GLOW, 0.4 + 0.6 * ga)
    for i in range(10):
        a = i * math.pi / 5 + t * 0.3
        line(c, CX, GROUND - 200, CX + math.cos(a) * 160, GROUND - 200 + math.sin(a) * 160, 8, GLOW, 0.35 * ga)
    # viajero de espaldas que camina hacia la puerta
    walker(c, CX - 40, GROUND + 140, 380, TEAL, t, 1)
    rrect(c, CX - 120, GROUND - 160, 60, 110, 14); fill(c, BROWN)
    if T > 16.0: tag(c, CX, PY + 110, "Vida larga o corta", NAVY, CREAM, 36, ease((T - 16.0) / 0.4) * (1 - ease((T - 19.3) / 0.3)))
    if T > 19.5: tag(c, CX, PY + 110, "La otra morada", GOLD_, CREAM, 40, ga)

def garden(c, x, base, t, a):
    gate(c, x, base, 230, 330, GOLD_, hx("BFE3C8"), a)
    for i in range(3):
        circle(c, x - 140 + i * 140, base - 40 - (i % 2) * 20, 50, GREEN, a)
    for i in range(6):
        k = (t * 0.4 + i / 6) % 1
        star(c, x - 100 + (i * 41) % 200, base - 330 - k * 80, 12 * math.sin(k * math.pi), GLOW, a)

def sc_fork(c, t, d):
    T = t + 21.4
    sky(c, hx("E9E3D5"), hx("F4EBDD"))
    ground(c, SAND)
    # dos caminos
    c.new_path(); c.move_to(CX - 60, PY + PH); c.curve_to(CX - 60, GROUND - 60, CX - 200, GROUND - 120, CX - 230, GROUND - 160); c.line_to(CX - 150, GROUND - 160)
    c.curve_to(CX - 120, GROUND - 100, CX + 30, GROUND - 60, CX + 60, PY + PH); c.close_path(); fill(c, hx("D8C3A0"))
    c.new_path(); c.move_to(CX - 40, PY + PH); c.curve_to(CX + 40, GROUND - 60, CX + 180, GROUND - 120, CX + 210, GROUND - 160); c.line_to(CX + 290, GROUND - 160)
    c.curve_to(CX + 230, GROUND - 100, CX + 90, GROUND - 60, CX + 60, PY + PH); c.close_path(); fill(c, hx("CBB596"))
    ga = ease(t / 0.8)
    garden(c, CX - 200, GROUND - 150, T, ga)
    for i in range(5):
        flame(c, CX + 150 + i * 60, GROUND - 150, 170 + 50 * math.sin(i * 1.7), T, i)
    tag(c, CX - 200, PY + 150, "Paraíso", GREEN, CREAM, 40, ga)
    tag(c, CX + 260, PY + 150, "Fuego", FIRE, CREAM, 40, ease((t - 0.4) / 0.6))
    if T > 23.2:
        k = ease((T - 23.2) / 0.5)
        with pop(c, CX, GROUND + 60, k):
            rrect(c, CX - 260, GROUND + 10, 520, 90, 45); fill(c, NAVY)
            text_c(c, "Rendición de cuentas", CX, GROUND + 70, 40, CREAM)

def sc_books(c, t, d):
    T = t + 27.3
    sky(c, hx("E7E1F0"), hx("F4EBDD"))
    ground(c, SAND)
    # libros que caen desde arriba y se reparten
    for i in range(6):
        st = i * 0.25
        k = clamp((t - st) / 1.4)
        if k <= 0: continue
        x = CX + (i - 2.5) * 140; y = PY + 160 + (k ** 2) * 200 + math.sin(t * 2 + i) * 10
        book(c, x, y, 0.6, [GREEN, NAVY, TERRA][i % 3], math.sin(t * 2 + i) * 0.3)
    # dos personas: derecha (verde) e izquierda
    walker(c, CX - 230, GROUND + 40, 420, TEAL, t, 0)
    walker(c, CX + 230, GROUND + 40, 420, hx("6B6B78"), t, 0, cap=GREY)
    if T > 29.2:
        k = ease((T - 29.2) / 0.5)
        book(c, CX - 230 + 110, GROUND - 260 - (1 - k) * 200, 0.75, GREEN)
        check(c, CX - 230, PY + 330, 44, (T - 29.6) / 0.4, GREEN)
        tag(c, CX - 230, GROUND + 90, "Derecha", GREEN, CREAM, 32, k)
    if T > 31.0:
        k = ease((T - 31.0) / 0.5)
        book(c, CX + 230 - 110, GROUND - 260 - (1 - k) * 200, 0.75, hx("6B6B78"))
        cross(c, CX + 230, PY + 330, 44, (T - 31.4) / 0.4)
        tag(c, CX + 230, GROUND + 90, "Izquierda", RED, CREAM, 32, k)

def sc_mizan(c, t, d):
    T = t + 33.5
    sky(c, hx("CFE3E0"), hx("EAF3EE"))
    ground(c, SAND)
    tilt = 0.26 * ease((T - 34.1) / 1.0) * math.cos(0) + 0.04 * math.sin(t * 2)
    (lx, ly), (rx, ry) = scale_(c, t, tilt, CX, PY + 330, GROUND)
    with pop(c, lx, ly + 150, (T - 34.1) / 0.5):
        for i in range(3): book(c, lx - 60 + i * 60, ly + 140, 0.55, GREEN)
    with pop(c, rx, ry + 150, (T - 35.3) / 0.5):
        book(c, rx, ry + 150, 0.4, hx("6B6B78"))
    tag(c, lx, PY + 120, "Pesa", GREEN, CREAM, 38, ease((T - 34.3) / 0.4))
    tag(c, rx, PY + 120, "Ligera", RED, CREAM, 38, ease((T - 35.5) / 0.4))

AYAT = [  # (inicio, fin, referencia, texto)
    (37.1, 39.5, "Corán 101:6", "فَأَمَّا مَن ثَقُلَتْ مَوَازِينُهُ"),
    (39.5, 40.7, "Corán 101:7", "فَهُوَ فِي عِيشَةٍ رَّاضِيَةٍ"),
    (40.7, 42.5, "Corán 101:8", "وَأَمَّا مَنْ خَفَّتْ مَوَازِينُهُ"),
    (42.5, 44.2, "Corán 101:9", "فَأُمُّهُ هَاوِيَةٌ"),
    (44.2, 46.1, "Corán 84:7", "فَأَمَّا مَنْ أُوتِيَ كِتَابَهُ بِيَمِينِهِ"),
    (46.1, 48.0, "Corán 84:8", "فَسَوْفَ يُحَاسَبُ حِسَابًا يَسِيرًا"),
    (48.0, 49.7, "Corán 84:9", "وَيَنقَلِبُ إِلَىٰ أَهْلِهِ مَسْرُورًا"),
    (49.7, 52.1, "Corán 69:25", "وَأَمَّا مَنْ أُوتِيَ كِتَابَهُ بِشِمَالِهِ فَيَقُولُ يَا لَيْتَنِي لَمْ أُوتَ كِتَابِيَهْ"),
]
AYAT_S = [arabic_surface(a[3], 66, NAVY, 600) for a in AYAT]

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
    circle(c, 0, 50, 18, GLOW); c.restore()

def sc_ayah(c, t, d):
    T = t + 37.1
    lantern(c, PX + 90, PY + 150, T, 0); lantern(c, PX + PW - 90, PY + 200, T, 1.5)
    arch_frame(c, CX, PY + 90, 720, 800, DKGREEN, CREAM)
    for i, (s, e, ref, _) in enumerate(AYAT):
        if not (s <= T < e): continue
        k = ease((T - s) / 0.4) * (ease((e - T) / 0.25) if i < len(AYAT) - 1 else 1)
        tag(c, CX, PY + 330, ref, GOLD_, CREAM, 34, k)
        sf = AYAT_S[i]
        blit(c, sf, CX, PY + 580 + (1 - k) * 30, k, min(1.0, 600 / sf.get_width(), 380 / sf.get_height()))
    rrect(c, CX - 200, PY + 820, 400, 12, 6); fill(c, GOLD_)

def warn_sign(c, x, y, s, col=SAND):
    c.new_path(); c.move_to(x, y - 120 * s); c.line_to(x + 140 * s, y + 110 * s); c.line_to(x - 140 * s, y + 110 * s); c.close_path(); fill(c, col)
    c.new_path(); c.move_to(x, y - 80 * s); c.line_to(x + 105 * s, y + 88 * s); c.line_to(x - 105 * s, y + 88 * s); c.close_path(); fill(c, NAVY)
    rrect(c, x - 12 * s, y - 40 * s, 24 * s, 80 * s, 12 * s); fill(c, col)
    circle(c, x, y + 62 * s, 14 * s, col)

def quran_open(c, x, y, s, col=DKGREEN):
    c.save(); c.translate(x, y); c.scale(s, s)
    line(c, -70, 40, 70, -10, 14, BROWN); line(c, 70, 40, -70, -10, 14, BROWN)
    for sd in (-1, 1):
        c.new_path(); c.move_to(0, 0); c.curve_to(sd * 40, -20, sd * 80, -18, sd * 110, -8)
        c.line_to(sd * 110, -90); c.curve_to(sd * 80, -100, sd * 40, -102, 0, -84); c.close_path(); fill(c, col)
        c.new_path(); c.move_to(0, -6); c.curve_to(sd * 40, -24, sd * 80, -22, sd * 100, -14)
        c.line_to(sd * 100, -86); c.curve_to(sd * 80, -94, sd * 40, -96, 0, -80); c.close_path(); fill(c, CREAM)
    c.restore()

def sc_reminder(c, t, d):
    T = t + 52.1
    sky(c, hx("F6E2C4"), hx("FBF1E0"))
    for i in range(14):
        a = i * math.pi / 7 + t * 0.15
        c.new_path(); c.move_to(CX, PY + 520); c.line_to(CX + math.cos(a) * 900 - math.sin(a) * 60, PY + 520 + math.sin(a) * 900 + math.cos(a) * 60)
        c.line_to(CX + math.cos(a) * 900 + math.sin(a) * 60, PY + 520 + math.sin(a) * 900 - math.cos(a) * 60); c.close_path(); fill(c, SAND, 0.25)
    with pop(c, CX, PY + 520, t / 0.6):
        quran_open(c, CX, PY + 560, 2.3)
    if T > 53.9: tag(c, CX, PY + 720, "Nos advirtió", TERRA, CREAM, 40, ease((T - 53.9) / 0.4))
    if T > 56.9: tag(c, CX, PY + 830, "El encuentro con Allah", NAVY, CREAM, 38, ease((T - 56.9) / 0.4))
    if T > 58.0: tag(c, CX, PY + 140, "Nos lo recordó", GOLD_, CREAM, 40, ease((T - 58.0) / 0.4))

def sc_danger(c, t, d):
    T = t + 60.6
    sky(c, hx("F2D3C6"), hx("F7E4DA"))
    ground(c, SAND)
    pulse = 1 + 0.06 * math.sin(t * 6)
    with pop(c, CX, PY + 300, t / 0.5):
        warn_sign(c, CX, PY + 300, 1.1 * pulse, FIRE2)
    if T > 62.3:
        k = ease((T - 62.3) / 0.5)
        book(c, CX - 220, GROUND - 200, 0.9, hx("6B6B78"), -0.2)
        tag(c, CX - 220, GROUND - 40, "Izquierda", RED, CREAM, 32, k)
    if T > 64.6:
        k = ease((T - 64.6) / 0.5)
        with pop(c, CX + 220, GROUND - 180, k):
            c.save(); c.translate(CX + 220, GROUND - 70); c.scale(0.4, 0.4)
            (lx, ly), (rx, ry) = scale_(c, t, 0.3, 0, -480, 0)
            book(c, rx, ry + 150, 0.4, hx("6B6B78"))
            for i in range(3): book(c, lx - 60 + i * 60, ly + 140, 0.5, GREY)
            c.restore()
        tag(c, CX + 220, GROUND - 40, "Ligera", RED, CREAM, 32, k)
    if T > 66.4:
        c.rectangle(PX, PY, PW, PH); c.set_source_rgba(*RED, 0.08 * (1 + math.sin(t * 8))); c.fill()
        tag(c, CX, PY + 560, "¡Cuidado, siervo de Allah!", RED, CREAM, 44, ease((T - 66.4) / 0.4))

def sc_prepare(c, t, d):
    T = t + 67.6
    sky(c, hx("CFE3E0"), hx("F3E6D2"))
    ground(c, OLIVE)
    # lista de preparación
    items = [(67.6, "Prepárate"), (69.5, "Examina tu alma"), (70.7, "Lucha contra ella")]
    for i, (st, txt) in enumerate(items):
        if T < st: continue
        k = ease((T - st) / 0.4)
        y = PY + 120 + i * 110
        rrect(c, CX - 330, y - 45, 660, 90, 26); fill(c, CREAM, k)
        check(c, CX - 270, y, 32, (T - st) / 0.4, GREEN)
        font(c, 40, True); c.move_to(CX - 210, y + 14); c.set_source_rgba(*NAVY, k); c.show_text(txt)
    # caminos de salvación y perdición
    if T > 72.3:
        k = ease((T - 72.3) / 0.5)
        tag(c, CX - 230, PY + 470, "Salvación: practícala", GREEN, CREAM, 32, k)
    if T > 74.9:
        k = ease((T - 74.9) / 0.5)
        tag(c, CX + 230, PY + 470, "Perdición: evítala", RED, CREAM, 32, k)
    walker(c, CX, GROUND + 40, 360, TEAL, t, 0, point=0)
    rrect(c, CX - 105, GROUND - 210, 50, 90, 12); fill(c, BROWN)
    if T > 77.2:
        k = (T - 77.2) / 0.5
        with pop(c, CX + 230, GROUND - 250, k):
            circle(c, CX + 230, GROUND - 250, 60, GOLD_); star(c, CX + 230, GROUND - 248, 36, CREAM)

SCENES = [
    (0.0, 7.3, sc_work, PANEL), (7.3, 13.0, sc_passing, PANEL), (13.0, 21.4, sc_moving, PANEL),
    (21.4, 27.3, sc_fork, PANEL), (27.3, 33.5, sc_books, PANEL), (33.5, 37.1, sc_mizan, PANEL),
    (37.1, 52.1, sc_ayah, SKY), (52.1, 60.6, sc_reminder, PANEL), (60.6, 67.6, sc_danger, PANEL),
    (67.6, SPEECH_END, sc_prepare, PANEL),
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
