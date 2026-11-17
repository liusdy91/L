"""Animación estilo cómic «¿No tienes tiempo para el Corán?» (1080x1920), subtítulos en español y marca «Casa Antigua».

Uso: python3 animacion_flat.py <video_o_audio_original> <salida.mp4> [segundo_preview]
"""
import math, subprocess, sys
import cairo

SRC = sys.argv[1]
OUT = sys.argv[2]
PREVIEW = float(sys.argv[3]) if len(sys.argv) > 3 else None
W, H, FPS = 1080, 1920, 30
SPEECH_END = 63.8
END_CARD = 4.0
TOTAL = SPEECH_END + END_CARD

def hx(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) / 255 for i in (0, 2, 4))

BG = hx("F4EBDD"); PANEL = hx("FBF6EE"); NAVY = hx("1F3A4D"); TEAL = hx("2A7F7A")
TERRA = hx("C8603C"); SAND = hx("E3B964"); OLIVE = hx("7E8B4F"); CREAM = hx("FFFDF8")
SKY = hx("CFE3E0"); RED = hx("D2453A"); BROWN = hx("8A5A3B"); GREY = hx("B9B2A6")
SKIN = hx("D9A47E")

SUBS = [
(0.0,1.5,"Hoy le preguntas a un musulmán:"),
(1.5,4.5,"«¿Cuánto has leído del *Corán* en tu día?»"),
(4.5,9.0,"Dice: «Por Allah, hoy no pude, estaba *ocupado*»."),
(9.0,11.0,"«Bien, ¿y cuántos *tuits* leíste?»"),
(11.0,16.5,"Dice: «Unos *mil*»."),
(16.5,19.5,"¿No tienes *tiempo* para leer el Corán?"),
(19.5,21.5,"¿Para leer la *palabra* *de* *Allah*,"),
(21.5,24.0,"que es toda *bendición*?"),
(24.0,25.5,"¡Por *Allah*!"),
(25.5,32.0,"Leer el Corán hace descender la *bendición* en el día."),
(32.0,34.5,"Y cuanto más leas del *Corán*,"),
(34.5,40.0,"más *bendición* habrá en tu día."),
(40.0,43.5,"Dices: «No tengo *tiempo* para leer el Corán»,"),
(43.5,45.5,"¡y sí tienes tiempo para leer *tuits*,"),
(45.5,49.0,"y leer esto y leer *aquello*!"),
(49.0,53.5,"Debemos *corregir*, oh hermanos, este asunto"),
(53.5,58.0,"y prestarle *atención*,"),
(58.0,SPEECH_END,"porque nos trae mucho *daño* y *mal*."),
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

import os, random
HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = cairo.ImageSurface.create_from_png(os.path.join(HERE, "logo_casa_antigua.png"))
SPEAKER = "SHEIJ SULAIMÁN AR-RUHAYLI"

# --- paleta de cómic
PAPER = hx("FFF4DC"); YEL = hx("FFD23F"); RED_ = hx("E63946"); BLUE = hx("1D7FD8"); CYAN = hx("4CC9F0")
INKK = hx("141414"); SKN = hx("E3A878"); GRN = hx("2A9D8F"); ORG = hx("F4A261"); PURP = hx("7B5EA7"); WHITE = (1, 1, 1)
GOLDC = hx("C9A060")

def cfont(c, size, kind="comic"):
    c.select_font_face("Bebas Neue" if kind == "bebas" else "Comic Neue", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    c.set_font_size(size)

def ctext(c, s, x, y, size, col=INKK, a=1.0, kind="comic", outline=0, ocol=INKK):
    cfont(c, size, kind); e = c.text_extents(s)
    c.new_path(); c.move_to(x - e.x_advance / 2, y)
    c.text_path(s)
    if outline:
        c.set_line_width(min(outline, size * 0.09)); c.set_line_join(cairo.LINE_JOIN_ROUND); c.set_source_rgba(*ocol, a); c.stroke_preserve()
    c.set_source_rgba(*col, a); c.fill()
    return e.x_advance

def wrap(c, s, size, maxw, kind="comic"):
    cfont(c, size, kind); words = s.split(); lines = [[]]
    for w in words:
        t = " ".join(lines[-1] + [w])
        if lines[-1] and c.text_extents(t).x_advance > maxw: lines.append([w])
        else: lines[-1].append(w)
    return [" ".join(l) for l in lines]

def fs(c, col, a=1.0, lw=7):
    """Relleno + contorno negro de cómic."""
    c.set_source_rgba(*col, a); c.fill_preserve()
    c.set_line_width(lw); c.set_line_join(cairo.LINE_JOIN_ROUND); c.set_source_rgba(*INKK, a); c.stroke()

def oline(c, x1, y1, x2, y2, w, col, a=1.0):
    line(c, x1, y1, x2, y2, w + 12, INKK, a); line(c, x1, y1, x2, y2, w, col, a)

# --- trama de puntos (halftone)
_dot = cairo.ImageSurface(cairo.FORMAT_ARGB32, 18, 18)
_dc = cairo.Context(_dot); _dc.arc(9, 9, 4.2, 0, 2 * math.pi); _dc.set_source_rgba(0, 0, 0, 1); _dc.fill()
def halftone(c, x, y, w, h, col, a=0.25, grad=True):
    c.save(); c.rectangle(x, y, w, h); c.clip()
    pat = cairo.SurfacePattern(_dot); pat.set_extend(cairo.EXTEND_REPEAT)
    c.push_group(); c.set_source_rgb(*col); c.paint(); g = c.pop_group()
    c.set_source(g)
    if grad:
        lg = cairo.LinearGradient(x, y, x + w, y + h); lg.add_color_stop_rgba(0, 0, 0, 0, a); lg.add_color_stop_rgba(1, 0, 0, 0, 0)
        c.push_group(); c.set_source(pat); c.paint(); c.set_operator(cairo.OPERATOR_DEST_IN); c.set_source(lg); c.paint(); m = c.pop_group()
        c.set_source(g); c.mask(m)
    else:
        c.push_group(); c.set_source(pat); c.paint_with_alpha(a); m = c.pop_group(); c.set_source(g); c.mask(m)
    c.restore()

def speed_lines(c, cx, cy, x, y, w, h, t, col=INKK, n=40, a=0.5):
    c.save(); c.rectangle(x, y, w, h); c.clip()
    rng = random.Random(int(t * 12))
    for i in range(n):
        ang = i * 2 * math.pi / n + rng.uniform(-0.05, 0.05)
        r0 = rng.uniform(220, 380)
        c.new_path(); c.move_to(cx + math.cos(ang) * r0, cy + math.sin(ang) * r0)
        c.line_to(cx + math.cos(ang - 0.02) * 1400, cy + math.sin(ang - 0.02) * 1400)
        c.line_to(cx + math.cos(ang + 0.02) * 1400, cy + math.sin(ang + 0.02) * 1400); c.close_path()
        c.set_source_rgba(*col, a); c.fill()
    c.restore()

def panel(c, x, y, w, h, bg, k, rot=0.0, dots=YEL):
    """Viñeta con borde negro y sombra; devuelve un context manager para dibujar dentro."""
    class _P:
        def __enter__(s):
            c.save(); s_ = 0.85 + 0.15 * back(k)
            cx, cy = x + w / 2, y + h / 2
            c.translate(cx, cy); c.rotate(rot * (1 - ease(k)) + rot * 0.15); c.scale(s_, s_); c.translate(-cx, -cy)
            c.push_group()
            rrect(c, x + 14, y + 16, w, h, 6); fill(c, INKK)
            rrect(c, x, y, w, h, 6); fill(c, bg)
            if dots: halftone(c, x, y, w, h, dots, 0.55)
            c.save(); rrect(c, x, y, w, h, 6); c.clip()
            return c
        def __exit__(s, *a):
            c.restore()
            c.new_path(); rrect(c, x, y, w, h, 6); c.set_line_width(10); c.set_source_rgb(*INKK); c.stroke()
            c.pop_group_to_source(); c.paint_with_alpha(clamp(ease(k * 1.8))); c.restore()
    return _P()

def bubble(c, x, y, w, h, txt, tx, ty, k, size=44, col=WHITE, kind="comic", tcol=INKK):
    """Globo de diálogo con cola hacia (tx, ty)."""
    if k <= 0: return
    with pop(c, x, y, k):
        c.new_path(); c.save(); c.translate(x, y); c.scale(w / 2, h / 2); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore()
        ang = math.atan2(ty - y, tx - x)
        bx, by = x + math.cos(ang) * w * 0.38, y + math.sin(ang) * h * 0.38
        px, py = -math.sin(ang) * 34, math.cos(ang) * 34
        c.move_to(bx + px, by + py); c.line_to(tx, ty); c.line_to(bx - px, by - py); c.close_path()
        c.set_fill_rule(cairo.FILL_RULE_WINDING)
        c.set_source_rgb(*INKK); c.set_line_width(14); c.stroke_preserve(); c.set_source_rgb(*col); c.fill()
        lines = wrap(c, txt, size, w * 0.78, kind)
        lh = size * 1.1; top = y - (len(lines) - 1) * lh / 2 + size * 0.35
        for i, l in enumerate(lines): ctext(c, l, x, top + i * lh, size, tcol, 1, kind)

def burst(c, x, y, r, txt, k, size=90, col=YEL, outer=RED_, t=0.0, tcol=RED_):
    if k <= 0: return
    with pop(c, x, y, k):
        for rr, colr in ((r * 1.18, outer), (r, col)):
            c.new_path()
            n = 16
            for i in range(n * 2):
                ang = i * math.pi / n + 0.05 * math.sin(t * 8)
                q = rr if i % 2 == 0 else rr * 0.68
                (c.move_to if i == 0 else c.line_to)(x + math.cos(ang) * q * 1.2, y + math.sin(ang) * q)
            c.close_path(); fs(c, colr, 1, 7)
        lines = txt.split("\n"); lh = size * 0.95
        for i, l in enumerate(lines):
            ctext(c, l, x, y + size * 0.35 + (i - (len(lines) - 1) / 2) * lh, size, tcol, 1, "bebas", outline=10, ocol=INKK)

def caption(c, x, y, txt, k, size=34, col=YEL):
    if k <= 0: return
    cfont(c, size); w = c.text_extents(txt).x_advance + 40
    with pop(c, x + w / 2, y, k):
        c.new_path(); c.rectangle(x, y - size, w, size * 1.5); fs(c, col, 1, 6)
        ctext(c, txt, x + w / 2, y + size * 0.15, size)

# --- personajes de cómic (sin rostro)
def cperson(c, x, feet, h, body, cap=WHITE, arm_r=0.3, arm_l=-0.3, lean=0.0, item=None, sweat=0.0, t=0.0, kufiya=None):
    c.save(); c.translate(x, feet); c.rotate(lean)
    hr = h * 0.12; bw = h * 0.38
    oline(c, -h * 0.08, -h * 0.3, -h * 0.09, -h * 0.02, h * 0.08, INKK)
    oline(c, h * 0.08, -h * 0.3, h * 0.09, -h * 0.02, h * 0.08, INKK)
    sy = -h * 0.66; L = h * 0.3
    # brazo izquierdo (detrás)
    oline(c, -bw * 0.42, sy, -bw * 0.42 + math.sin(arm_l) * L, sy + math.cos(arm_l) * L, h * 0.07, body)
    c.new_path(); c.move_to(-bw / 2, -h * 0.28); c.line_to(bw / 2, -h * 0.28)
    c.curve_to(bw / 2, -h * 0.55, bw * 0.4, -h * 0.76, 0, -h * 0.76)
    c.curve_to(-bw * 0.4, -h * 0.76, -bw / 2, -h * 0.55, -bw / 2, -h * 0.28); c.close_path(); fs(c, body)
    # brillo de tinta
    line(c, -bw * 0.28, -h * 0.62, -bw * 0.32, -h * 0.4, 6, WHITE, 0.6)
    hx_, hy_ = bw * 0.42 + math.sin(arm_r) * L, sy + math.cos(arm_r) * L
    oline(c, bw * 0.42, sy, hx_, hy_, h * 0.07, body)
    c.new_path(); c.arc(hx_, hy_, h * 0.045, 0, 2 * math.pi); fs(c, SKN, 1, 5)
    if item: item(c, hx_, hy_, h)
    c.new_path(); c.arc(0, -h * 0.76 - hr * 0.95, hr, 0, 2 * math.pi); fs(c, SKN)
    if kufiya:
        c.new_path(); c.move_to(-hr * 1.25, -h * 0.72); c.curve_to(-hr * 1.5, -h * 0.76 - hr * 2.6, hr * 1.5, -h * 0.76 - hr * 2.6, hr * 1.25, -h * 0.72); c.close_path(); fs(c, kufiya)
        c.new_path(); c.save(); c.translate(0, -h * 0.76 - hr * 0.8); c.scale(0.72, 0.85); c.arc(0, 0, hr, 0, 2 * math.pi); c.restore(); fs(c, SKN, 1, 5)
    elif cap:
        c.new_path(); c.arc(0, -h * 0.76 - hr * 1.05, hr * 1.02, math.pi, 2 * math.pi); c.close_path(); fs(c, cap, 1, 6)
    if sweat > 0:
        for i in range(3):
            k = (t * 1.5 + i / 3) % 1
            sx, sy2 = hr * 1.3 + i * 12, -h * 0.76 - hr * 1.5 + k * 60
            c.new_path(); c.move_to(sx, sy2 - 16); c.curve_to(sx + 10, sy2, sx + 10, sy2 + 8, sx, sy2 + 8); c.curve_to(sx - 10, sy2 + 8, sx - 10, sy2, sx, sy2 - 16)
            fs(c, CYAN, sweat * (1 - k), 3)
    c.restore()

def phone(c, x, y, s, t=0.0, glow=0.0, rot=0.0, scroll=0.0):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    if glow:
        for i in range(4): circle(c, 0, 0, 120 + i * 30, CYAN, 0.08 * glow)
    rrect(c, -70, -130, 140, 260, 22); fs(c, INKK, 1, 6)
    rrect(c, -58, -110, 116, 220, 10); fill(c, hx("EAF6FF"))
    c.save(); rrect(c, -58, -110, 116, 220, 10); c.clip()
    off = (scroll * 120) % 70
    for i in range(-1, 5):
        yy = -100 + i * 70 - off
        rrect(c, -50, yy, 100, 58, 8); fill(c, WHITE); c.new_path(); rrect(c, -50, yy, 100, 58, 8); c.set_line_width(2); c.set_source_rgb(*INKK); c.stroke()
        circle(c, -34, yy + 16, 9, BLUE)
        rrect(c, -18, yy + 10, 58, 8, 4); fill(c, hx("9AA9B8")); rrect(c, -40, yy + 34, 80, 8, 4); fill(c, hx("C8D2DC"))
    c.restore(); c.restore()

def phone_item(c, x, y, h):
    phone(c, x + 10, y - 40, h / 900, rot=-0.15)

def mushaf_c(c, x, y, s, open_=1.0, dust=0.0, glow=0.0, t=0.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    if glow > 0:
        for i in range(14):
            a = i * math.pi / 7 + t * 0.4
            c.new_path(); c.move_to(0, -60); c.line_to(math.cos(a) * 420 - math.sin(a) * 30, -60 + math.sin(a) * 420 + math.cos(a) * 30)
            c.line_to(math.cos(a) * 420 + math.sin(a) * 30, -60 + math.sin(a) * 420 - math.cos(a) * 30); c.close_path(); fill(c, YEL, 0.5 * glow)
    if open_ < 0.5:
        rrect(c, -110, -150, 220, 170, 10); fs(c, GRN)
        rrect(c, -80, -120, 160, 110, 8); c.set_line_width(5); c.set_source_rgb(*YEL); c.stroke()
        if dust > 0:
            for i in range(9): circle(c, -90 + i * 22, -152 - (i % 3) * 4, 6, hx("B8AC94"), dust)
            c.new_path(); c.move_to(110, -150); c.line_to(160, -200); c.move_to(110, -150); c.line_to(170, -150); c.move_to(110, -150); c.line_to(150, -110)
            c.set_line_width(2); c.set_source_rgba(*INKK, 0.6 * dust); c.stroke()
    else:
        for sd in (-1, 1):
            c.new_path(); c.move_to(0, 0); c.curve_to(sd * 50, -24, sd * 100, -22, sd * 150, -10)
            c.line_to(sd * 150, -130); c.curve_to(sd * 100, -142, sd * 50, -144, 0, -120); c.close_path(); fs(c, GRN)
            c.new_path(); c.move_to(0, -8); c.curve_to(sd * 50, -30, sd * 100, -28, sd * 136, -18)
            c.line_to(sd * 136, -122); c.curve_to(sd * 100, -132, sd * 50, -134, 0, -112); c.close_path(); fs(c, WHITE, 1, 4)
            for i in range(5): line(c, sd * 24 if sd > 0 else -118, -98 + i * 18, sd * 118 if sd > 0 else -24, -98 + i * 18, 4, hx("8B8B8B"))
    c.restore()

def sparkle(c, x, y, r, col=YEL, a=1.0):
    if r <= 0: return
    c.new_path(); c.move_to(x, y - r); c.curve_to(x + r * 0.15, y - r * 0.15, x + r * 0.15, y - r * 0.15, x + r, y)
    c.curve_to(x + r * 0.15, y + r * 0.15, x + r * 0.15, y + r * 0.15, x, y + r)
    c.curve_to(x - r * 0.15, y + r * 0.15, x - r * 0.15, y + r * 0.15, x - r, y)
    c.curve_to(x - r * 0.15, y - r * 0.15, x - r * 0.15, y - r * 0.15, x, y - r); fs(c, col, a, 4)

def clock(c, x, y, r, t):
    c.new_path(); c.arc(x, y, r, 0, 2 * math.pi); fs(c, WHITE)
    for i in range(12):
        a = i * math.pi / 6; line(c, x + math.cos(a) * r * 0.8, y + math.sin(a) * r * 0.8, x + math.cos(a) * r * 0.9, y + math.sin(a) * r * 0.9, 4, INKK)
    line(c, x, y, x + math.cos(t * 6) * r * 0.7, y + math.sin(t * 6) * r * 0.7, 6, RED_)
    line(c, x, y, x + math.cos(t * 0.5) * r * 0.45, y + math.sin(t * 0.5) * r * 0.45, 8, INKK)

# --- escenas (T absoluto). Escenario: y 380..1400
X0, Y0, WW, HH = 50, 380, 980, 1020

def sc1(c, T):  # 0–4.5: la pregunta
    with panel(c, X0, Y0, WW, 480, CYAN, T / 0.4, -0.04):
        cperson(c, 260, Y0 + 470, 400, BLUE, arm_r=-1.4)
        cperson(c, 780, Y0 + 470, 400, ORG, item=phone_item)
        bubble(c, 520, Y0 + 110, 520, 170, "¿Cuánto Corán leíste hoy?", 330, Y0 + 210, (T - 1.5) / 0.4, 48)
    with panel(c, X0 + 40, Y0 + 520, WW - 80, 470, YEL, (T - 0.3) / 0.4, 0.03, dots=ORG):
        speed_lines(c, X0 + WW / 2, Y0 + 760, X0 + 40, Y0 + 520, WW - 80, 470, T, INKK, 36, 0.12)
        mushaf_c(c, X0 + WW / 2, Y0 + 830, 1.3, 1.0, glow=0.4, t=T)
    caption(c, X0 + 20, Y0 + 30, "HOY...", T / 0.4)

def sc2(c, T):  # 4.5–9: «estaba ocupado»
    with panel(c, X0, Y0, WW, HH, hx("FFE8C2"), (T - 4.5) / 0.4, 0.03, dots=ORG):
        cperson(c, X0 + WW / 2, Y0 + HH - 60, 620, ORG, arm_r=-2.0, arm_l=2.0, sweat=1, t=T, item=None)
        clock(c, X0 + 190, Y0 + 300, 90, T); clock(c, X0 + WW - 190, Y0 + 520, 70, T * 1.3)
        bubble(c, X0 + WW / 2 + 40, Y0 + 180, 720, 230, "¡Por Allah, hoy no pude, estaba ocupado!", X0 + WW / 2, Y0 + 340, (T - 5.0) / 0.4, 50)
        if T > 6.5: ctext(c, "TIC TAC", X0 + WW - 200, Y0 + 680, 70, RED_, ease((T - 6.5) / 0.3), "bebas", outline=8)

def sc3(c, T):  # 9–16.5: ¿cuántos tuits? — «unos mil»
    with panel(c, X0, Y0, WW, HH, hx("D9EEFF"), (T - 9.0) / 0.4, -0.03, dots=CYAN):
        speed_lines(c, X0 + WW / 2, Y0 + 560, X0, Y0, WW, HH, T, BLUE, 44, 0.12)
        phone(c, X0 + WW / 2, Y0 + 580, 2.4, T, glow=1, scroll=T * 3)
        bubble(c, X0 + 290, Y0 + 140, 460, 170, "¿Y cuántos tuits leíste?", X0 + 360, Y0 + 300, (T - 9.2) / 0.4, 46)
        n = int(clamp((T - 11.0) / 2.5) * 1000)
        if T > 11.0:
            burst(c, X0 + WW - 250, Y0 + 260, 170, f"¡UNOS\n{n}!", (T - 11.0) / 0.4, 84, t=T)
        for i in range(6):
            k = ((T - 11) * 0.8 + i / 6) % 1
            if T > 11: sparkle(c, X0 + 120 + i * 150, Y0 + HH - 80 - k * 300, 20, YEL, 1 - k)

def sc4(c, T):  # 16.5–24: ¿no tienes tiempo para la palabra de Allah?
    k1 = (T - 16.5) / 0.4
    with panel(c, X0, Y0, WW / 2 - 15, HH, hx("E9E1D2"), k1, -0.05, dots=hx("B8AC94")):
        op = clamp((T - 19.5) / 0.6)
        mushaf_c(c, X0 + WW / 4, Y0 + 640, 1.2, op, dust=1 - op, glow=op * (1 if T > 21.5 else 0.5), t=T)
        if T > 21.5:
            for i in range(8):
                k = ((T - 21.5) * 0.7 + i / 8) % 1
                sparkle(c, X0 + 60 + (i * 73) % 380, Y0 + 640 - k * 420, 22, YEL, 1 - k)
        caption(c, X0 + 20, Y0 + 50, "LA PALABRA DE ALLAH" if T > 19.5 else "OLVIDADO...", k1, 30)
    with panel(c, X0 + WW / 2 + 15, Y0, WW / 2 - 15, HH, hx("D9EEFF"), (T - 16.8) / 0.4, 0.05, dots=CYAN):
        phone(c, X0 + WW * 0.75, Y0 + 600, 1.5, T, glow=1, scroll=T * 3)
    burst(c, X0 + WW / 2, Y0 + 220, 160, "¿NO TIENES\nTIEMPO?", (T - 17.0) / 0.4, 58, t=T)

def sc5(c, T):  # 24–25.5: ¡Por Allah!
    with panel(c, X0, Y0, WW, HH, RED_, (T - 24.0) / 0.25, 0.0, dots=hx("9B1D27")):
        speed_lines(c, X0 + WW / 2, Y0 + HH / 2, X0, Y0, WW, HH, T, WHITE, 50, 0.35)
        burst(c, X0 + WW / 2, Y0 + HH / 2, 300, "¡POR\nALLAH!", (T - 24.0) / 0.3, 150, col=YEL, outer=WHITE, t=T)

def sc6(c, T):  # 25.5–40: leer el Corán trae baraka
    with panel(c, X0, Y0, WW, 640, hx("FFF0B8"), (T - 25.5) / 0.4, -0.03, dots=YEL):
        # sol de un nuevo día
        c.new_path(); c.arc(X0 + WW - 170, Y0 + 150, 80, 0, 2 * math.pi); fs(c, YEL)
        for i in range(12):
            a = i * math.pi / 6 + T * 0.3
            oline(c, X0 + WW - 170 + math.cos(a) * 105, Y0 + 150 + math.sin(a) * 105, X0 + WW - 170 + math.cos(a) * 135, Y0 + 150 + math.sin(a) * 135, 8, YEL)
        cperson(c, X0 + 330, Y0 + 620, 440, GRN, arm_r=-1.2, arm_l=1.0)
        mushaf_c(c, X0 + 470, Y0 + 400, 0.8, 1.0, glow=0.6, t=T)
        # bendición que desciende
        for i in range(14):
            k = ((T - 25.5) * 0.5 + i / 14) % 1
            sparkle(c, X0 + 80 + (i * 67) % (WW - 160), Y0 + 40 + k * 560, 18 + 6 * (i % 3), YEL, math.sin(k * math.pi))
        caption(c, X0 + 20, Y0 + 40, "LA BENDICIÓN DESCIENDE", (T - 26.0) / 0.4, 30)
    with panel(c, X0 + 30, Y0 + 680, WW - 60, 330, WHITE, (T - 26.5) / 0.4, 0.03, dots=CYAN):
        if T < 34.5: ctext(c, "BARAKA DEL DÍA", X0 + WW / 2, Y0 + 770, 60, BLUE, 1, "bebas")
        lvl = clamp((T - 27.0) / 5.0) * 0.45 + clamp((T - 32.0) / 6.0) * 0.55
        rrect(c, X0 + 90, Y0 + 800, WW - 180, 80, 40); fs(c, WHITE)
        if lvl > 0.02:
            rrect(c, X0 + 98, Y0 + 808, (WW - 196) * lvl, 64, 32); fs(c, YEL, 1, 4)
        for i in range(int(lvl * 8) + 1):
            mushaf_c(c, X0 + 140 + i * 105, Y0 + 980, 0.32, 1.0)
        if T > 34.5: ctext(c, "¡MÁS LECTURA = MÁS BARAKA!", X0 + WW / 2, Y0 + 770, 60, RED_, ease((T - 34.5) / 0.4), "bebas", outline=6, ocol=WHITE)

def sc7(c, T):  # 40–49: no tienes tiempo… pero sí para tuits
    with panel(c, X0, Y0, WW / 2 - 15, 560, hx("E9E1D2"), (T - 40.0) / 0.4, -0.04, dots=hx("B8AC94")):
        mushaf_c(c, X0 + WW / 4, Y0 + 420, 1.0, 0.0, dust=1.0)
        bubble(c, X0 + WW / 4, Y0 + 150, 400, 160, "«No tengo tiempo»", X0 + WW / 4 + 40, Y0 + 260, (T - 40.3) / 0.4, 44)
    with panel(c, X0 + WW / 2 + 15, Y0, WW / 2 - 15, 560, hx("D9EEFF"), (T - 43.5) / 0.4, 0.04, dots=CYAN):
        cperson(c, X0 + WW * 0.75, Y0 + 540, 380, ORG, item=phone_item, arm_r=-0.9)
        if T > 43.7: ctext(c, "¡PERO PARA TUITS SÍ!", X0 + WW * 0.75, Y0 + 80, 44, RED_, ease((T - 43.7) / 0.4), "bebas", outline=8)
    with panel(c, X0, Y0 + 600, WW, 420, YEL, (T - 45.5) / 0.4, 0.02, dots=ORG):
        speed_lines(c, X0 + WW / 2, Y0 + 810, X0, Y0 + 600, WW, 420, T, INKK, 40, 0.15)
        for i in range(7):
            ph = ((T - 45.5) * 0.9 + i / 7) % 1
            phone(c, X0 + 80 + ph * (WW - 160), Y0 + 810 + math.sin(i * 2) * 80, 0.55, T, scroll=T * 4, rot=math.sin(i + T) * 0.3)
        ctext(c, "¡ESTO! ¡AQUELLO! ¡SCROLL!", X0 + WW / 2, Y0 + 690, 60, BLUE, ease((T - 45.8) / 0.3), "bebas", outline=8, ocol=WHITE)

def sc8(c, T):  # 49–58: corrijamos, hermanos
    with panel(c, X0, Y0, WW, HH, hx("DFF5EC"), (T - 49.0) / 0.4, -0.02, dots=GRN):
        swap = ease((T - 50.5) / 1.0)
        for i, col in enumerate((BLUE, GRN, ORG)):
            x = X0 + 210 + i * 280
            cperson(c, x, Y0 + HH - 70, 470, col, arm_r=lerp(0.3, -1.1, swap), arm_l=-0.3,
                    item=(lambda cc, hx_, hy_, h: mushaf_c(cc, hx_ + 10, hy_ + 30, 0.42, 1.0)) if swap > 0.5 else phone_item)
        burst(c, X0 + WW / 2, Y0 + 210, 200, "¡CORRIJAMOS!", (T - 49.3) / 0.4, 76, t=T)
        if T > 53.5:
            burst(c, X0 + WW - 160, Y0 + 430, 110, "¡ATENCIÓN!", (T - 53.5) / 0.4, 46, col=CYAN, outer=BLUE, tcol=WHITE, t=T)

def sc9(c, T):  # 58–fin: trae daño y mal
    with panel(c, X0, Y0, WW, HH, hx("3B3355"), (T - 58.0) / 0.4, 0.03, dots=PURP):
        # nube de tormenta sobre el teléfono
        for dx, dy, r in ((-150, 0, 120), (-30, -50, 150), (120, -10, 130), (230, 30, 90), (-250, 40, 80)):
            c.new_path(); c.arc(X0 + WW / 2 + dx, Y0 + 260 + dy, r, 0, 2 * math.pi); fs(c, hx("6B6585"))
        flash = max(0, math.sin((T - 58) * 3.0)) ** 10
        c.new_path(); bx, by = X0 + WW / 2 + 40, Y0 + 360
        c.move_to(bx, by); c.line_to(bx - 70, by + 200); c.line_to(bx - 10, by + 190); c.line_to(bx - 60, by + 380); c.line_to(bx + 90, by + 150); c.line_to(bx + 20, by + 160); c.line_to(bx + 60, by)
        c.close_path(); fs(c, YEL, 0.4 + 0.6 * flash)
        phone(c, X0 + WW / 2, Y0 + 800, 1.3, T, scroll=T * 2)
        if T > 58.5: burst(c, X0 + 230, Y0 + 640, 140, "¡CRACK!", (T - 58.5) / 0.3, 70, t=T)
        if T > 59.5:
            caption(c, X0 + 30, Y0 + HH - 50, "DAÑO Y MAL", (T - 59.5) / 0.4, 44, col=RED_)

SCENES8 = [(0, 4.5, sc1), (4.5, 9.0, sc2), (9.0, 16.5, sc3), (16.5, 24.0, sc4), (24.0, 25.5, sc5),
           (25.5, 40.0, sc6), (40.0, 49.0, sc7), (49.0, 58.0, sc8), (58.0, SPEECH_END, sc9)]

# --- marca, cabecera, subtítulos, cierre
def logo_img(c, x, y, size, a=1.0, round_=True):
    c.save()
    if round_:
        c.new_path(); c.arc(x, y, size / 2, 0, 2 * math.pi); c.clip()
    sc = size / LOGO.get_width()
    c.translate(x - size / 2, y - size / 2); c.scale(sc, sc)
    c.set_source_surface(LOGO, 0, 0); c.get_source().set_filter(cairo.FILTER_BEST)
    c.paint_with_alpha(a); c.restore()

def watermark(c):
    circle(c, 112, 128, 76, INKK); circle(c, 112, 128, 70, GOLDC); circle(c, 112, 128, 66, (0, 0, 0))
    logo_img(c, 112, 128, 132, 1.0)
    ctext(c, "CASA ANTIGUA", 350, 152, 70, WHITE, 1, "bebas", outline=7)

def header(c, t):
    k = ease(t / 0.6)
    c.save(); c.translate(W / 2, 290); c.rotate(-0.02)
    c.new_path(); c.rectangle(-330, -42, 660, 74); fs(c, RED_, k, 7)
    ctext(c, SPEAKER, 0, 18, 50, WHITE, k, "bebas")
    c.restore()
    rrect(c, 120, 340, W - 240, 16, 8); fs(c, WHITE, 1, 5)
    rrect(c, 124, 344, (W - 248) * clamp(t / SPEECH_END), 8, 4); fill(c, RED_)

def subtitle(c, t):
    for s, e, txt in SUBS:
        if not (s <= t < e): continue
        size = 50
        toks = [(w.replace("*", ""), "*" in w) for w in txt.split()]
        cfont(c, size); sp = c.text_extents(" ").x_advance
        lines = [[]]; cw = 0
        for wd, hl in toks:
            w = c.text_extents(wd).x_advance
            if lines[-1] and cw + sp + w > 880: lines.append([]); cw = 0
            cw += (sp if lines[-1] else 0) + w; lines[-1].append((wd, hl, w))
        lh = size * 1.2
        bh = len(lines) * lh + 50; top = 1620 - bh / 2
        kb = ease((t - s) / 0.2) * (ease((e - t) / 0.15) if e - t < 0.15 else 1)
        c.save(); c.translate(W / 2, top + bh / 2); c.rotate(0.012); c.scale(0.9 + 0.1 * kb, 0.9 + 0.1 * kb); c.translate(-W / 2, -(top + bh / 2))
        c.new_path(); c.rectangle(60 + 12, top + 12, W - 120, bh); fill(c, INKK, kb)
        c.new_path(); c.rectangle(60, top, W - 120, bh); fs(c, YEL, kb, 7)
        n = sum(len(l) for l in lines); span = min((e - s) * 0.5, 0.1 * n + 0.2); idx = 0
        for li, ln in enumerate(lines):
            lw = sum(w for _, _, w in ln) + sp * (len(ln) - 1); x = (W - lw) / 2
            for wd, hl, w in ln:
                st = s + span * idx / max(1, n); idx += 1
                k = (t - st) / 0.22
                if k > 0:
                    sc = 0.5 + 0.5 * back(k)
                    c.save(); c.translate(x + w / 2, top + 25 + li * lh + size * 0.85); c.scale(sc, sc)
                    cfont(c, size); c.new_path(); c.move_to(-w / 2, 0); c.text_path(wd)
                    c.set_source_rgba(*(RED_ if hl else INKK), ease(k) * kb); c.fill(); c.restore()
                x += w + sp
        c.restore()

def end_card(c, t):
    k = ease(t / 0.8)
    c.set_source_rgb(0, 0, 0); c.paint()
    for i in range(12):
        a = i * math.pi / 6 + t * 0.2
        line(c, W / 2, 800, W / 2 + math.cos(a) * 900, 800 + math.sin(a) * 900, 60, GOLDC, 0.05)
    with pop(c, W / 2, 800, t / 0.7):
        logo_img(c, W / 2, 800, 820, 1.0, round_=False)
    text_c(c, "Casa Antigua", W / 2, 1320 + (1 - k) * 40, 100, GOLDC, k)
    k2 = ease((t - 0.8) / 0.6)
    rrect(c, W / 2 - 260, 1410, 520, 110, 55); fill(c, GOLDC, k2)
    text_c(c, "Suscríbete", W / 2, 1484, 54, (0, 0, 0), k2)

def frame(c, t):
    if t >= SPEECH_END:
        end_card(c, t - SPEECH_END); return
    c.set_source_rgb(*PAPER); c.paint()
    halftone(c, 0, 0, W, H, ORG, 0.35)
    for s, e, fn in SCENES8:
        if s <= t < e: fn(c, t)
    header(c, t)
    subtitle(c, t)
    watermark(c)

surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
ctx = cairo.Context(surf)
ctx.set_antialias(cairo.ANTIALIAS_BEST)
if PREVIEW is not None:
    frame(ctx, PREVIEW); surf.write_to_png(OUT); sys.exit()
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", SRC, "-map", "0:v", "-map", "1:a",
    "-af", f"atrim=0:{SPEECH_END},afade=t=out:st={SPEECH_END-0.5}:d=0.5,apad",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "160k", "-t", str(TOTAL), "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
nf = int(TOTAL * FPS)
for i in range(nf):
    frame(ctx, i / FPS); surf.flush()
    enc.stdin.write(bytes(surf.get_data()))
enc.stdin.close(); enc.wait(); print("frames", nf)
