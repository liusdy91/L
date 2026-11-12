"""Animación «noche y oro» con apariciones del sheij (1080x1920), subtítulos en español y marca de agua «Casa Antigua».

Uso: python3 animacion_flat.py <video_o_audio_original> <salida.mp4> [segundo_preview]
"""
import math, subprocess, sys
import cairo

SRC = sys.argv[1]
OUT = sys.argv[2]
PREVIEW = float(sys.argv[3]) if len(sys.argv) > 3 else None
W, H, FPS = 1080, 1920, 30
SPEECH_END = 64.3
END_CARD = 4.0
TOTAL = SPEECH_END + END_CARD

def hx(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) / 255 for i in (0, 2, 4))

BG = hx("F4EBDD"); PANEL = hx("FBF6EE"); NAVY = hx("1F3A4D"); TEAL = hx("2A7F7A")
TERRA = hx("C8603C"); SAND = hx("E3B964"); OLIVE = hx("7E8B4F"); CREAM = hx("FFFDF8")
SKY = hx("CFE3E0"); RED = hx("D2453A"); BROWN = hx("8A5A3B"); GREY = hx("B9B2A6")
SKIN = hx("D9A47E")

SUBS = [
(0.0,2.0,"No memorices *mucho* de golpe,"),
(2.0,4.5,"porque quien memoriza *mucho*"),
(4.5,7.0,"lo *olvida* rápidamente."),
(7.0,9.0,"Más bien, memoriza *cinco* *aleyas*."),
(9.0,12.5,"Y siempre digo: empieza con *poco*."),
(12.5,13.5,"Dite a ti mismo:"),
(13.5,15.5,"«Memorizaré *una* *aleya* al día, nada más»."),
(15.5,17.0,"«Memorizaré solo *una* *aleya*»."),
(17.0,19.0,"«Pero *tengo* que memorizar una aleya»."),
(19.0,21.0,"Si ves que *estás* *memorizando*,"),
(21.0,21.6,"entonces, durante el *día*,"),
(21.6,23.0,"ocúpate de esa *aleya*."),
(23.0,25.0,"Memoriza *dos* aleyas."),
(25.0,26.0,"Si ves que *puedes*,"),
(26.0,27.5,"memoriza *tres* aleyas,"),
(27.5,30.0,"memoriza *cuatro*, *cinco* aleyas."),
(30.0,31.0,"Muchos de nosotros, hasta ahora,"),
(31.0,32.5,"no han memorizado el *Corán*"),
(32.5,34.5,"porque *no* *quisieron*."),
(34.5,36.5,"Si no, Allah ha hecho el Corán *fácil*."),
(36.5,40.0,"Si tan solo te *comprometieras* a memorizar"),
(40.0,41.0,"*una* *aleya* al día..."),
(41.0,42.5,"No pienses que así no completarás el *Corán*."),
(42.5,43.0,"¡*No*!"),
(43.0,44.5,"*Comprométete* a memorizar"),
(44.5,46.0,"*una* *aleya* al día,"),
(46.0,47.0,"y, por Allah, *memorizarás*."),
(47.0,48.5,"Memorizarás la *aleya*,"),
(48.5,52.0,"luego le *añadirás* otra aleya."),
(52.0,55.5,"Y si puedes, que sean *dos* aleyas al día."),
(55.5,59.0,"Pero algunos quieren empezar y memorizarlo *todo*,"),
(59.0,60.5,"y por eso dicen: «*No* *puedo*»."),
(60.5,61.5,"Claro,"),
(61.5,63.0,"empezar hoy y tenerlo memorizado *mañana*:"),
(63.0,SPEECH_END,"eso *no* *es* *posible*."),
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

import os, io
from PIL import Image as _PImage, ImageDraw as _PDraw, ImageFont as _PFont
HERE = os.path.dirname(os.path.abspath(__file__))
SPEAKER = "Sheij Sulaimán ar-Ruhayli"
LOGO = cairo.ImageSurface.create_from_png(os.path.join(HERE, "logo_casa_antigua.png"))
_AR_FONT = os.path.join(HERE, "fuentes", "Amiri-Bold.ttf")

# --- paleta «noche y oro» (la del logo de Casa Antigua)
INK = hx("110F0C"); INK2 = hx("1D1913"); GOLD = hx("C9A060"); GOLD2 = hx("E8C987"); CREAMT = hx("F3EAD8")
DIM = hx("6E6455"); ROSE = hx("D9604A"); JADE = hx("4FA58A")

# Clips del sheij: (inicio, fin) en segundos
CLIPS = [(0.0, 2.0), (9.0, 12.5), (30.0, 34.5), (42.5, 47.0), (59.0, 61.5)]

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

NUMS = {n: arabic_surface(s, 54, INK) for n, s in enumerate("٠١٢٣٤٥٦٧٨٩")}
AYAH_5417 = arabic_surface("وَلَقَدْ يَسَّرْنَا الْقُرْآنَ لِلذِّكْرِ فَهَلْ مِن مُّدَّكِرٍ", 64, GOLD2, 640)

# --------------------------------------------------------------- dibujo base
def star8(c, x, y, r, col, a=1.0, lw=None):
    c.new_path()
    for i in range(16):
        rr = r if i % 2 == 0 else r * 0.78
        ang = i * math.pi / 8
        (c.move_to if i == 0 else c.line_to)(x + math.cos(ang) * rr, y + math.sin(ang) * rr)
    c.close_path()
    if lw: c.set_line_width(lw); c.set_source_rgba(*col, a); c.stroke()
    else: fill(c, col, a)

def marker(c, x, y, r, n=None, a=1.0, glow=0.0):
    """Marcador de aleya: estrella de ocho puntas dorada con el número en cifras árabes."""
    if glow > 0:
        for i in range(4): circle(c, x, y, r * (1.3 + i * 0.25), GOLD2, 0.08 * glow * a)
    star8(c, x, y, r, GOLD, a)
    circle(c, x, y, r * 0.66, CREAMT, a)
    c.new_path(); c.arc(x, y, r * 0.58, 0, 2 * math.pi); c.set_line_width(r * 0.06); c.set_source_rgba(*GOLD, a); c.stroke()
    if n is not None:
        blit(c, NUMS[n], x, y + r * 0.06, a, r / 80)

def tag(c, x, y, txt, bg, fg, size=34, a=1.0):
    font(c, size, True); w = c.text_extents(txt).x_advance + size * 1.4
    rrect(c, x - w / 2, y - size * 0.95, w, size * 1.7, size * 0.85); fill(c, bg, a)
    text_c(c, txt, x, y + size * 0.3, size, fg, a)

def check(c, x, y, r, k, col=JADE):
    with pop(c, x, y, k):
        circle(c, x, y, r, col)
        c.new_path(); c.set_line_width(r * 0.22); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.move_to(x - r * 0.45, y + r * 0.02); c.line_to(x - r * 0.1, y + r * 0.38); c.line_to(x + r * 0.5, y - r * 0.35); c.set_source_rgb(*CREAMT); c.stroke()

def cross(c, x, y, r, k):
    with pop(c, x, y, k):
        circle(c, x, y, r, ROSE)
        line(c, x - r * 0.4, y - r * 0.4, x + r * 0.4, y + r * 0.4, r * 0.22, CREAMT)
        line(c, x - r * 0.4, y + r * 0.4, x + r * 0.4, y - r * 0.4, r * 0.22, CREAMT)

def mushaf(c, x, y, s, open_=1.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    line(c, -80, 50, 80, -10, 16, hx("7A5A3A")); line(c, 80, 50, -80, -10, 16, hx("7A5A3A"))
    for sd in (-1, 1):
        c.new_path(); c.move_to(0, 0); c.curve_to(sd * 40, -20, sd * 80, -18, sd * 120, -8)
        c.line_to(sd * 120, -100); c.curve_to(sd * 80, -110, sd * 40, -112, 0, -94); c.close_path(); fill(c, GOLD)
        c.new_path(); c.move_to(0, -6); c.curve_to(sd * 40, -24, sd * 80, -22, sd * 108, -14)
        c.line_to(sd * 108, -94); c.curve_to(sd * 80, -102, sd * 40, -104, 0, -88); c.close_path(); fill(c, CREAMT)
        for i in range(4): rrect(c, sd * 20 if sd > 0 else -92, -78 + i * 16, 72, 6, 3); fill(c, GOLD, 0.6)
    c.restore()

def figure(c, x, feet, h, col=GOLD, lean=0.0, arms=0.0):
    person(c, x, feet, h, col, cap=CREAMT, lean=lean, wave=arms)

def background(c, t):
    c.set_source_rgb(*INK); c.paint()
    g = cairo.RadialGradient(W / 2, 900, 50, W / 2, 900, 1100)
    g.add_color_stop_rgba(0, *INK2, 1); g.add_color_stop_rgba(1, *INK, 1)
    c.rectangle(0, 0, W, H); c.set_source(g); c.fill()
    # celosía de estrellas de ocho puntas, muy tenue
    off = (t * 10) % 180
    for iy in range(-1, 12):
        for ix in range(-1, 7):
            star8(c, ix * 180 + 90 + (iy % 2) * 90 - off * 0.3, iy * 180 + off, 62, GOLD, 0.05, lw=2)

# --------------------------------------------------------------- escenas (T = tiempo absoluto)
SX, SY, SW, SH = 60, 400, 960, 960   # escenario
SCX, SCY = SX + SW / 2, SY + SH / 2
FLOOR = SY + SH - 120

def sc_much(c, T):
    """Mucho de golpe → se escapa."""
    t = T - 2.0
    # vasija
    vx, vy = SCX, FLOOR - 40
    c.new_path(); c.move_to(vx - 210, vy - 330); c.line_to(vx + 210, vy - 330); c.curve_to(vx + 200, vy - 120, vx + 150, vy, vx, vy)
    c.curve_to(vx - 150, vy, vx - 200, vy - 120, vx - 210, vy - 330); c.close_path(); fill(c, hx("3A3126"))
    rrect(c, vx - 230, vy - 350, 460, 34, 17); fill(c, GOLD)
    slip = clamp((T - 4.5) / 2.5)
    for i in range(22):
        st = i * 0.09
        k = clamp((t - st) / 0.7)
        if k <= 0: continue
        col_i, row_i = i % 5, i // 5
        tx, ty = vx - 160 + col_i * 80, vy - 80 - row_i * 70
        x = lerp(vx + (i % 3 - 1) * 60, tx, ease(k)); y = lerp(SY + 40, ty, ease(k))
        # se escapan: salen por arriba y se desvanecen
        if slip > 0 and i % 2 == 0 or (slip > 0.4 and i % 3 == 0):
            e = clamp(slip * 1.6 - (i % 7) * 0.08)
            x += (i % 2 * 2 - 1) * 380 * e; y -= 300 * e - 500 * e * e
            a = 1 - e
        else:
            a = 1
        if a > 0: marker(c, x, y, 34, (i % 9) + 1, a)
    if T > 4.5: tag(c, SCX, SY + 60, "Se olvida rápido", ROSE, CREAMT, 40, ease((T - 4.5) / 0.4))
    else: tag(c, SCX, SY + 60, "Mucho de golpe", DIM, CREAMT, 40, ease(t / 0.4))

def sc_five(c, T):
    t = T - 7.0
    for i in range(5):
        x = SCX - 320 + i * 160
        with pop(c, x, SCY, (t - i * 0.18) / 0.4):
            marker(c, x, SCY, 64, i + 1, glow=1)
    check(c, SCX, SCY + 190, 50, (t - 1.2) / 0.4)
    tag(c, SCX, SY + 120, "Solo cinco aleyas", GOLD, INK, 42, ease(t / 0.4))

def calendar(c, x, y, w, h, label, a=1.0):
    rrect(c, x - w / 2, y - h / 2, w, h, 30); fill(c, CREAMT, a)
    rrect(c, x - w / 2, y - h / 2, w, 110, 30); fill(c, ROSE, a)
    rrect(c, x - w / 2, y - h / 2 + 70, w, 40, 0); fill(c, ROSE, a)
    for sx in (-1, 1): rrect(c, x + sx * w * 0.28 - 10, y - h / 2 - 30, 20, 60, 10); fill(c, DIM, a)
    text_c(c, label, x, y - h / 2 + 76, 50, CREAMT, a)

def sc_one(c, T):
    t = T - 12.5
    with pop(c, SCX, SCY, t / 0.5):
        calendar(c, SCX, SCY + 20, 520, 560, "Día 1")
    k = (T - 13.5) / 0.5
    if k > 0:
        lock = ease((T - 17.0) / 0.5)
        marker(c, SCX, SCY + 90, 110 * (0.6 + 0.4 * back(k)), 1, ease(k), glow=lock)
    if T > 15.5: tag(c, SCX, SY + 40, "Solo una", GOLD, INK, 40, ease((T - 15.5) / 0.4) * (1 - ease((T - 16.8) / 0.3)))
    if T > 17.0:
        tag(c, SCX, SY + 40, "¡Pero sin falta!", JADE, CREAMT, 40, ease((T - 17.0) / 0.4))
        check(c, SCX + 220, SCY + 260, 46, (T - 17.2) / 0.4)

def sc_day(c, T):
    t = T - 19.0
    u = clamp(t / 4.0)
    ax, ay = SCX, FLOOR - 40
    c.new_path(); c.arc(ax, ay, 400, math.pi, 2 * math.pi); c.set_line_width(4); c.set_dash([14, 14]); c.set_source_rgba(*GOLD, 0.4); c.stroke(); c.set_dash([])
    a = math.pi + u * math.pi
    sx, sy = ax + math.cos(a) * 400, ay + math.sin(a) * 400
    for i in range(10):
        b = i * math.pi / 5 + t
        line(c, sx + math.cos(b) * 70, sy + math.sin(b) * 70, sx + math.cos(b) * 95, sy + math.sin(b) * 95, 10, GOLD2)
    circle(c, sx, sy, 56, GOLD2)
    # la aleya se repite durante el día: ondas
    for i in range(3):
        k = (t * 0.7 + i / 3) % 1
        c.new_path(); c.arc(ax, ay - 120, 90 + k * 160, 0, 2 * math.pi); c.set_line_width(5); c.set_source_rgba(*GOLD, 0.5 * (1 - k)); c.stroke()
    marker(c, ax, ay - 120, 90, 1, glow=1)
    figure(c, ax - 300, FLOOR + 40, 300, JADE)
    figure(c, ax + 300, FLOOR + 40, 300, JADE)
    tag(c, SCX, SY + 40, "Todo el día con esa aleya", GOLD, INK, 36, ease(t / 0.4))

def sc_count(c, T):
    t = T - 23.0
    steps = [(23.0, 2), (26.0, 3), (27.5, 4), (28.3, 5)]
    for i, (st, n) in enumerate(steps):
        k = (T - st) / 0.5
        if k <= 0: continue
        x = SX + 60 + i * 205; top = FLOOR - 80 - i * 130
        with pop(c, x + 90, FLOOR, k):
            rrect(c, x, top, 200, FLOOR - top + 40, 16); fill(c, hx("3A3126"))
            rrect(c, x, top, 200, 18, 9); fill(c, GOLD)
            marker(c, x + 100, top - 70, 52, n, glow=1)
    # figura que sube los escalones
    cur = max([i for i, (st, _) in enumerate(steps) if T >= st] + [0])
    fx = SX + 160 + cur * 205; ftop = FLOOR - 80 - cur * 130
    figure(c, fx - 60, ftop + 2, 220, JADE)
    if T > 25.0 and T < 26.0: tag(c, SCX, SY + 40, "¿Puedes? Sube un escalón", GOLD, INK, 36, ease((T - 25.0) / 0.3))

def sc_easy(c, T):
    t = T - 34.5
    with pop(c, SCX, SCY + 160, t / 0.5):
        mushaf(c, SCX, SCY + 220, 2.0)
    rrect(c, SX + 60, SY + 80, SW - 120, 330, 40); fill(c, hx("2A241C"))
    c.new_path(); rrect(c, SX + 60, SY + 80, SW - 120, 330, 40); c.set_line_width(4); c.set_source_rgba(*GOLD, 0.8); c.stroke()
    blit(c, AYAH_5417, SCX, SY + 230, ease(t / 0.6), min(1.0, 760 / AYAH_5417.get_width()))
    tag(c, SCX, SY + 80, "Corán 54:17", GOLD, INK, 30, ease(t / 0.5))
    if T > 35.3: text_c(c, "«Hemos hecho el Corán fácil para recordar»", SCX, SY + 470, 34, GOLD2, ease((T - 35.3) / 0.5), bold=False)

def sc_commit(c, T):
    t = T - 36.5
    # 30 días: cada día se enciende un marcador
    n = int(clamp(t / 4.0) * 30)
    for i in range(30):
        x = SX + 120 + (i % 6) * 144; y = SY + 150 + (i // 6) * 140
        if i < n: marker(c, x, y, 46, (i % 9) + 1, glow=0.4)
        else: circle(c, x, y, 30, DIM, 0.35)
    tag(c, SCX, SY + 40, "Una aleya cada día", GOLD, INK, 38, ease(t / 0.4))
    if T > 41.0:
        k = ease((T - 41.0) / 0.4)
        rrect(c, SX + 80, FLOOR - 150, SW - 160, 130, 40); fill(c, hx("2A241C"), k)
        text_c(c, "¿Así nunca terminaré?", SCX, FLOOR - 70, 50, GOLD2, k)

def sc_add(c, T):
    t = T - 47.0
    # cadena que crece + anillo de progreso alrededor del mushaf
    n = 1 + (1 if T > 48.5 else 0) + int(clamp((T - 52.0) / 3.0) * 6) * 2 // 2
    p = clamp((T - 47.0) / 8.5)
    cx, cy = SCX, SCY - 60
    c.new_path(); c.arc(cx, cy, 250, 0, 2 * math.pi); c.set_line_width(26); c.set_source_rgba(*GOLD, 0.15); c.stroke()
    c.new_path(); c.arc(cx, cy, 250, -math.pi / 2, -math.pi / 2 + 2 * math.pi * p * 0.6); c.set_line_width(26); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_source_rgb(*GOLD2); c.stroke()
    mushaf(c, cx, cy + 60, 1.4)
    for i in range(min(n, 8)):
        x = SCX - 7 * 55 + i * 110
        with pop(c, x, FLOOR - 40, (T - (47.0 if i == 0 else 48.5 if i == 1 else 52.0 + (i - 2) * 0.45)) / 0.4):
            marker(c, x, FLOOR - 40, 44, i + 1)
            if i > 0: text_c(c, "+", x - 55, FLOOR - 25, 40, GOLD2)
    if T > 52.0: tag(c, SCX, SY + 40, "Dos aleyas al día", JADE, CREAMT, 38, ease((T - 52.0) / 0.4))
    else: tag(c, SCX, SY + 40, "Memorizarás", GOLD, INK, 40, ease(t / 0.4))

def sc_rush(c, T):
    t = T - 55.5
    # montaña de aleyas que alguien quiere subir de un salto
    for i in range(6):
        w = 640 - i * 100
        rrect(c, SCX - w / 2 + 120, FLOOR - (i + 1) * 95, w, 95, 14); fill(c, hx("3A3126") if i % 2 else hx("463B2D"))
        for j in range(int(w / 110)):
            marker(c, SCX - w / 2 + 175 + j * 110, FLOOR - (i + 1) * 95 + 48, 30, None, 0.8)
    mushaf(c, SCX + 120, FLOOR - 600, 0.9)
    # carrera y salto que no llega
    u = clamp(t / 2.4)
    jx = lerp(SX + 120, SCX - 120, u)
    jy = FLOOR + 30 - math.sin(u * math.pi) * 380 * (1 if u < 1 else 0)
    if t > 2.4:
        f = clamp((t - 2.4) / 0.6)
        jx = SCX - 120 - 100 * f; jy = FLOOR + 30
    figure(c, jx, jy, 260, JADE, lean=-0.3 if t > 2.4 else 0.15, arms=0.8)
    if t > 2.6: cross(c, SCX - 260, SY + 220, 50, (t - 2.6) / 0.4)
    tag(c, SCX, SY + 40, "Todo de golpe", ROSE, CREAMT, 40, ease(t / 0.4))

def sc_impossible(c, T):
    t = T - 61.5
    with pop(c, SCX - 220, SCY - 40, t / 0.4):
        calendar(c, SCX - 220, SCY - 40, 340, 380, "Hoy")
        marker(c, SCX - 220, SCY + 40, 60, 1)
    with pop(c, SCX + 220, SCY - 40, (t - 0.3) / 0.4):
        calendar(c, SCX + 220, SCY - 40, 340, 380, "Mañana")
        mushaf(c, SCX + 220, SCY + 100, 0.9)
    line(c, SCX - 40, SCY - 40, SCX + 40, SCY - 40, 10, GOLD2)
    if T > 63.0:
        cross(c, SCX, SCY - 40, 90, (T - 63.0) / 0.4)
        tag(c, SCX, FLOOR - 40, "No es posible", ROSE, CREAMT, 48, ease((T - 63.0) / 0.4))

SCENES2 = [(2.0, 7.0, sc_much), (7.0, 9.0, sc_five), (12.5, 19.0, sc_one), (19.0, 23.0, sc_day), (23.0, 30.0, sc_count),
           (34.5, 36.5, sc_easy), (36.5, 42.5, sc_commit), (47.0, 55.5, sc_add), (55.5, 59.0, sc_rush), (61.5, SPEECH_END, sc_impossible)]

# --------------------------------------------------------------- el sheij en un marco de arco
CW, CH = 760, 760
def arch_path(c, x, top, w, h):
    c.new_path(); c.move_to(x - w / 2, top + h); c.line_to(x - w / 2, top + w * 0.42)
    c.curve_to(x - w / 2, top + w * 0.12, x - w * 0.12, top + 20, x, top)
    c.curve_to(x + w * 0.12, top + 20, x + w / 2, top + w * 0.12, x + w / 2, top + w * 0.42)
    c.line_to(x + w / 2, top + h); c.close_path()

def draw_clip(c, frame_surf, k, T):
    x, top = SCX, SY + 60
    s = 0.92 + 0.08 * ease(k)
    c.save(); c.translate(x, top + CH / 2); c.scale(s, s); c.translate(-x, -(top + CH / 2))
    c.push_group()
    arch_path(c, x, top - 18, CW + 36, CH + 36); fill(c, GOLD)
    arch_path(c, x, top, CW, CH); c.save(); c.clip()
    c.translate(x - CW / 2, top); c.set_source_surface(frame_surf, 0, 0); c.get_source().set_filter(cairo.FILTER_BEST); c.paint()
    c.restore()
    # degradado inferior para fundir con el fondo
    g = cairo.LinearGradient(0, top + CH - 200, 0, top + CH)
    g.add_color_stop_rgba(0, *INK, 0); g.add_color_stop_rgba(1, *INK, 0.85)
    arch_path(c, x, top, CW, CH); c.set_source(g); c.fill()
    tag(c, x, top + CH - 50, SPEAKER, GOLD, INK, 34)
    c.pop_group_to_source(); c.paint_with_alpha(ease(k)); c.restore()

# --------------------------------------------------------------- marca, cabecera, subtítulos, cierre
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

def header(c, t):
    text_c(c, "Memorizar el Corán poco a poco", W / 2, 290, 40, CREAMT, ease(t / 0.8))
    rrect(c, 120, 322, W - 240, 8, 4); fill(c, GOLD, 0.15)
    rrect(c, 120, 322, (W - 240) * clamp(t / SPEECH_END), 8, 4); fill(c, GOLD)

def subtitle(c, t):
    for s, e, txt in SUBS:
        if not (s <= t < e): continue
        size = 58
        lines, sp = layout_sub(c, txt, size, 940)
        if len(lines) > 3:
            size = 50; lines, sp = layout_sub(c, txt, size, 960)
        lh = size * 1.3
        top = 1440 + (360 - len(lines) * lh) / 2
        n = sum(len(l) for l in lines); span = min((e - s) * 0.55, 0.11 * n + 0.2)
        out = ease((e - t) / 0.15) if e - t < 0.15 else 1
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
                    font(c, size, True); c.move_to(-w / 2, -size * 0.02)
                    c.set_source_rgba(*(GOLD2 if hl else CREAMT), ease(k) * out); c.show_text(word); c.restore()
                    if hl:
                        rrect(c, x, top + li * lh + size * 0.92, w * ease(k), 6, 3); fill(c, GOLD, out)
                x += w + sp

def layout_sub(c, text, size, maxw):
    font(c, size, True); sp = c.text_extents(" ").x_advance
    toks = [(w.replace("*", ""), "*" in w) for w in text.split()]
    lines = [[]]; cw = 0
    for tk in toks:
        w = c.text_extents(tk[0]).x_advance
        if lines[-1] and cw + sp + w > maxw: lines.append([]); cw = 0
        cw += (sp if lines[-1] else 0) + w; lines[-1].append((tk[0], tk[1], w))
    return lines, sp

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

def clip_alpha(t):
    for s, e in CLIPS:
        if s - 0.01 <= t < e:
            return min(1.0, (t - s) / 0.35 + (1 if s == 0 else 0), (e - t) / 0.3)
    return 0.0

def frame(c, t, clip_surf):
    if t >= SPEECH_END:
        end_card(c, t - SPEECH_END); return
    background(c, t)
    ca = clip_alpha(t)
    if ca < 1:
        c.save(); c.rectangle(SX, SY - 20, SW, SH + 40); c.clip()
        c.push_group()
        for s, e, fn in SCENES2:
            if s <= t < e:
                fn(c, t)
        c.pop_group_to_source()
        # cuando entra una escena tras un clip, aparece suavemente
        c.paint_with_alpha(1 - ca); c.restore()
    if ca > 0 and clip_surf is not None:
        draw_clip(c, clip_surf, ca, t)
    header(c, t)
    subtitle(c, t)
    watermark(c)

# --------------------------------------------------------------- render
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
ctx = cairo.Context(surf)
ctx.set_antialias(cairo.ANTIALIAS_BEST)

def clip_decoder():
    # recorte que evita los subtítulos en inglés y la franja con la marca del canal original
    return subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf",
        f"crop=280:280:40:0,scale={CW}:{CH}:flags=lanczos,unsharp=5:5:0.6,eq=saturation=0.9:contrast=1.05",
        "-f", "rawvideo", "-pix_fmt", "bgra", "-r", str(FPS), "-"], stdout=subprocess.PIPE)

if PREVIEW is not None:
    dec = clip_decoder(); fb = CW * CH * 4; cs = None
    for i in range(int(PREVIEW * FPS) + 1):
        raw = dec.stdout.read(fb)
        if len(raw) < fb: break
        last = raw
    dec.kill()
    cs = cairo.ImageSurface.create_for_data(bytearray(last), cairo.FORMAT_ARGB32, CW, CH, CW * 4)
    frame(ctx, PREVIEW, cs); surf.write_to_png(OUT); sys.exit()

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", SRC, "-map", "0:v", "-map", "1:a",
    "-af", f"atrim=0:{SPEECH_END},afade=t=out:st={SPEECH_END-0.6}:d=0.6,apad",
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "160k", "-t", str(TOTAL), "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
dec = clip_decoder(); fb = CW * CH * 4; last = None
nf = int(TOTAL * FPS)
for i in range(nf):
    raw = dec.stdout.read(fb) if dec else b""
    if len(raw) == fb: last = raw
    cs = cairo.ImageSurface.create_for_data(bytearray(last), cairo.FORMAT_ARGB32, CW, CH, CW * 4) if last else None
    frame(ctx, i / FPS, cs); surf.flush()
    enc.stdin.write(bytes(surf.get_data()))
enc.stdin.close(); enc.wait(); print("frames", nf)
