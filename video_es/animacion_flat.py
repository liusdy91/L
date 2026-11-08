"""Animación flat vector (1080x1920) con subtítulos en español y marca de agua «Casa Antigua».

Uso: python3 animacion_flat.py <video_o_audio_original> <salida.mp4> [segundo_preview]
"""
import math, subprocess, sys
import cairo

SRC = sys.argv[1]
OUT = sys.argv[2]
PREVIEW = float(sys.argv[3]) if len(sys.argv) > 3 else None
W, H, FPS = 1080, 1920, 30
SPEECH_END = 85.0
END_CARD = 4.0
TOTAL = SPEECH_END + END_CARD

def hx(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) / 255 for i in (0, 2, 4))

BG = hx("F4EBDD"); PANEL = hx("FBF6EE"); NAVY = hx("1F3A4D"); TEAL = hx("2A7F7A")
TERRA = hx("C8603C"); SAND = hx("E3B964"); OLIVE = hx("7E8B4F"); CREAM = hx("FFFDF8")
SKY = hx("CFE3E0"); RED = hx("D2453A"); BROWN = hx("8A5A3B"); GREY = hx("B9B2A6")
SKIN = hx("D9A47E")

SUBS = [
(0.0,4.5,"Es tal que, si una persona estudia las letras del *idioma* *inglés*,"),
(4.5,7.0,"ni hablar de aprender a formar *oraciones* con las palabras,"),
(7.0,10.5,"se vuelve *orgullosa* y *presumida*."),
(10.5,16.8,"Es más, algunos enseñan a sus *hijos* el *idioma* *inglés*."),
(16.8,20.2,"Si el niño quiere dar el *salam*, su padre le dice:"),
(20.2,24.1,"«No, no digas *As-Salamu* *Alaikum*, di *bye* *bye*»."),
(24.1,27.0,"¿Qué es *«bye* *bye»*?"),
(27.0,29.8,"Esto es porque «bye bye» es el *idioma* de la gente"),
(29.8,33.0,"que tiene la *superioridad* que posee,"),
(33.0,35.8,"mientras que nosotros somos *débiles*."),
(35.8,38.5,"¿Hemos llegado a *este* *nivel*?..."),
(38.5,41.3,"En vez de *Ma'a* *Salama* o *As-Salamu* *Alaikum*, el niño dice:"),
(41.3,44.0,"...*bye* *bye*, *bye* *bye*..."),
(44.0,48.4,"(Y es a *Allah* a quien se pide ayuda) ¿Por qué pasa esto? Porque su *padre* se lo enseñó,"),
(48.4,52.6,"y el niño vive según lo que su *padre* le *enseña*."),
(52.6,57.2,"En todo caso, oh hermanos, digo: es *obligatorio* buscar *fuerza* y *poder* a través de nuestra *religión*,"),
(57.2,61.3,"porque el *poder* pertenece a *Allah*, a Su *Mensajero* (la paz sea con él)"),
(61.3,69.1,"y a los *creyentes*. Y no debemos seguirlos en asuntos que *no* *traen* *beneficio*."),
(69.1,77.3,"En cuanto a seguirlos en asuntos *industriales* y en lo que *Allah* ha puesto en la *tierra*,"),
(77.3,SPEECH_END,"esto no se critica; al contrario, se *fomenta*, y podemos ser *líderes* en ello junto con establecer nuestra *religión*."),
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

def sc_book(c, t, d):
    ground(c, SAND)
    k = ease(t / 0.6)
    bx, by = CX, GROUND - 60
    with pop(c, bx, by, t / 0.6):
        for s in (-1, 1):
            c.new_path(); c.move_to(bx, by); c.curve_to(bx + s * 120, by - 40, bx + s * 230, by - 30, bx + s * 300, by - 10)
            c.line_to(bx + s * 300, by - 210); c.curve_to(bx + s * 230, by - 230, bx + s * 120, by - 240, bx, by - 200); c.close_path()
            fill(c, CREAM)
            for i in range(5):
                line(c, bx + s * 60, by - 170 + i * 30, bx + s * 250, by - 160 + i * 30, 6, GREY, 0.7)
        line(c, bx, by, bx, by - 200, 6, TERRA)
    letters = "ABCDEFGH"
    phase2 = clamp((t - 4.5) / 1.0)
    for i, L in enumerate(letters):
        st = 0.5 + i * 0.35
        u = ease((t - st) / 1.4)
        if u <= 0: continue
        ang = -1.2 + i * 0.35
        fx = bx + math.cos(ang - math.pi / 2) * 0 + (i - 3.5) * 70 * u
        fy = by - 220 - 420 * math.sin(u * math.pi / 2) + 30 * math.sin(t * 2 + i)
        # en la fase 2 se acomodan en fila (formar oraciones)
        tx, ty = CX - 3.5 * 95 + i * 95, PY + 170 + (0 if i < 4 else 0)
        x = lerp(fx, tx, ease_io(phase2)); y = lerp(fy, ty, ease_io(phase2))
        col = [TERRA, TEAL, NAVY, SAND][i % 4]
        c.save(); c.translate(x, y); c.rotate((1 - phase2) * 0.3 * math.sin(t * 3 + i))
        rrect(c, -40, -40, 80, 80, 16); fill(c, col)
        text_c(c, L, 0, 18, 52, CREAM); c.restore()
    if phase2 > 0:
        rrect(c, CX - 380, PY + 240, 760 * ease(phase2), 14, 7); fill(c, TEAL, 0.8)

def sc_proud(c, t, d):
    ground(c)
    fx, fy = CX, GROUND + 40
    # cola de pavo real abriéndose
    o = ease(t / 1.2)
    cols = [TEAL, SAND, TERRA, OLIVE]
    for i in range(11):
        a = -math.pi / 2 + (i - 5) * 0.3 * o
        L = 400 * o
        ex, ey = fx + math.sin(a + math.pi / 2) * 0 + math.cos(a) * L, fy - 260 + math.sin(a) * L
        line(c, fx, fy - 260, ex, ey, 34, cols[i % 4], 0.9)
        circle(c, ex, ey, 30 * o, cols[(i + 2) % 4]); circle(c, ex, ey, 13 * o, NAVY)
    chest = 1 + 0.25 * ease((t - 0.8) / 1)
    person(c, fx, fy, 560, TEAL, chest=chest, head_tilt=-0.25 * ease((t - 1) / 0.8), cap=CREAM)
    # destellos
    for i in range(6):
        k = (t * 0.9 + i / 6) % 1
        ang = i * 1.05 + 0.4
        x, y = fx + math.cos(ang) * 300, fy - 420 + math.sin(ang) * 220
        star(c, x, y, 26 * math.sin(k * math.pi), SAND)
    # corona
    with pop(c, fx, fy - 600, (t - 1.6) / 0.5):
        c.new_path(); x0, y0 = fx - 60, fy - 612
        c.move_to(x0, y0 + 40); c.line_to(x0, y0); c.line_to(x0 + 30, y0 + 22); c.line_to(x0 + 60, y0 - 12)
        c.line_to(x0 + 90, y0 + 22); c.line_to(x0 + 120, y0); c.line_to(x0 + 120, y0 + 40); c.close_path(); fill(c, SAND)

def star(c, x, y, r, col, a=1.0):
    if r <= 0: return
    c.new_path()
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.42
        ang = -math.pi / 2 + i * math.pi / 5
        (c.move_to if i == 0 else c.line_to)(x + math.cos(ang) * rr, y + math.sin(ang) * rr)
    c.close_path(); fill(c, col, a)

def sc_board(c, t, d):
    ground(c, SAND)
    with pop(c, CX + 120, PY + 330, t / 0.6):
        rrect(c, CX - 200, PY + 140, 540, 360, 18); fill(c, BROWN)
        rrect(c, CX - 180, PY + 160, 500, 320, 10); fill(c, TEAL)
        letters = "A B C"
        n = int(clamp((t - 0.8) / 2.5) * len(letters) + 0.999)
        text_c(c, letters[:n], CX + 70, PY + 360, 120, CREAM)
        if t > 3.5: text_c(c, "hello", CX + 70, PY + 450, 60, SAND, ease((t - 3.5) / 0.5))
    with pop(c, CX - 260, GROUND + 40, (t - 0.3) / 0.6):
        person(c, CX - 260, GROUND + 40, 620, NAVY, point=ease((t - 1) / 0.6), cap=CREAM)
    with pop(c, CX + 150, GROUND + 40, (t - 0.6) / 0.6):
        person(c, CX + 150, GROUND + 40, 340, TERRA, head_tilt=0.1 * math.sin(t * 2))

def sc_salam(c, t, d):
    ground(c)
    person(c, CX - 230, GROUND + 40, 620, NAVY, cap=CREAM)
    person(c, CX + 200, GROUND + 40, 340, TERRA, wave=ease(t / 0.8) * (0.7 + 0.3 * math.sin(t * 6)))
    with pop(c, CX + 220, PY + 420, (t - 0.4) / 0.5):
        bubble(c, CX + 200, PY + 420, 520, 120, "As-Salamu Alaikum", TEAL, CREAM, 46, tail=1)
    x = (t - 3.4) / 0.4
    if x > 0:  # tachado
        k = ease(x)
        line(c, CX - 80, PY + 370, CX - 80 + 560 * k, PY + 470, 16, RED)
        line(c, CX - 80, PY + 470, CX - 80 + 560 * k, PY + 370, 16, RED)
    with pop(c, CX - 200, PY + 200, (t - 3.6) / 0.5):
        bubble(c, CX - 160, PY + 200, 360, 120, "Bye bye!", SAND, NAVY, 56, tail=-1)

def sc_question(c, t, d):
    b = abs(math.sin(t * 3.2)) * 60
    with pop(c, CX, CY, t / 0.5):
        font(c, 520, True)
        c.save(); c.translate(CX, CY + 170 - b); c.rotate(0.08 * math.sin(t * 2.5))
        e = c.text_extents("?"); c.move_to(-e.x_advance / 2, 0); c.set_source_rgb(*TERRA); c.show_text("?")
        c.restore()
    circle(c, CX, GROUND + 70, 120 - b * 0.6, NAVY, 0.15)
    with pop(c, CX + 250, PY + 190, (t - 0.6) / 0.5):
        bubble(c, CX + 220, PY + 190, 300, 100, "bye bye", SAND, NAVY, 46, tail=-1)

def sc_scale(c, t, d):
    ground(c, SAND)
    w = 2.8  # empieza 'débiles' en 33.0 -> local 6.0
    tilt = 0.28 * ease((t - 0.5) / 1.2) + 0.06 * ease((t - 6.0) / 0.8)
    px_, py_ = CX, PY + 330
    rrect(c, px_ - 20, py_, 40, GROUND - py_, 10); fill(c, BROWN)
    rrect(c, px_ - 140, GROUND - 20, 280, 40, 16); fill(c, BROWN)
    arm = 340
    lx, ly = px_ - math.cos(tilt) * arm, py_ + math.sin(tilt) * arm
    rx, ry = px_ + math.cos(tilt) * arm, py_ - math.sin(tilt) * arm
    line(c, lx, ly, rx, ry, 18, NAVY); circle(c, px_, py_, 24, SAND)
    for (x, y) in ((lx, ly), (rx, ry)):
        line(c, x, y, x - 100, y + 200, 4, NAVY); line(c, x, y, x + 100, y + 200, 4, NAVY)
        c.new_path(); c.move_to(x - 130, y + 200); c.line_to(x + 130, y + 200); c.curve_to(x + 100, y + 250, x - 100, y + 250, x - 130, y + 200); fill(c, NAVY)
    # lado pesado: torres y corona (superioridad)
    with pop(c, lx, ly + 200, (t - 2.8) / 0.6):
        for i, hh in enumerate((150, 210, 120)):
            rrect(c, lx - 100 + i * 70, ly + 200 - hh, 60, hh, 6); fill(c, [TERRA, TEAL, OLIVE][i])
            for j in range(int(hh / 40)):
                rrect(c, lx - 88 + i * 70, ly + 200 - hh + 15 + j * 38, 36, 18, 3); fill(c, CREAM, 0.8)
    with pop(c, rx, ry + 200, (t - 6.0) / 0.6):
        person(c, rx, ry + 198, 150, GREY)
    text_c(c, "ellos", lx, PY + 120, 46, TERRA, ease((t - 3) / 0.5))
    text_c(c, "nosotros", rx, PY + 120, 46, TEAL, ease((t - 6.2) / 0.5))

def sc_stairs(c, t, d):
    steps = 6; sw, sh = 130, 90
    x0, y0 = PX + 110, PY + 260
    for i in range(steps):
        rrect(c, x0 + i * sw, y0 + i * sh, sw + 4, PY + PH - (y0 + i * sh) - 30, 0); fill(c, [SAND, TERRA][i % 2], 0.85)
    u = clamp(t / 2.4) * (steps - 1)
    i = int(u); f = u - i
    bx = x0 + (i + f) * sw + sw / 2
    by = y0 + i * sh - 40 - math.sin(f * math.pi) * 60 + (sh * f if f > 0.5 else 0) * 0
    by = y0 + (i + ease_io(f)) * sh - 40 - math.sin(f * math.pi) * 50
    circle(c, bx, by, 38, TEAL)
    with pop(c, CX + 260, PY + 160, t / 0.5):
        rrect(c, CX + 170, PY + 90, 180, 140, 20); fill(c, NAVY)
        line(c, CX + 260, PY + 120, CX + 260, PY + 200, 14, CREAM)
        c.new_path(); c.move_to(CX + 230, PY + 175); c.line_to(CX + 290, PY + 175); c.line_to(CX + 260, PY + 215); c.close_path(); fill(c, CREAM)

def sc_byebye(c, t, d):
    ground(c)
    person(c, CX, GROUND + 40, 380, TERRA, wave=ease((t - 2.8) / 0.4) * (0.7 + 0.3 * math.sin(t * 7)))
    olds = [("Ma'a Salama", CX - 220, PY + 200), ("As-Salamu Alaikum", CX + 140, PY + 360)]
    for j, (s, x, y) in enumerate(olds):
        k = clamp((t - 0.3 - j * 0.5) / 0.5)
        gone = clamp((t - 2.6) / 0.35)
        if gone >= 1: continue
        with pop(c, x, y, k, a=1 - gone):
            bubble(c, x, y, 40 + len(s) * 24, 104, s, TEAL, CREAM, 42, tail=1 if j == 0 else -1)
    spots = [(-260, 170), (230, 150), (-300, 420), (280, 400), (0, 260), (-120, 560), (180, 600)]
    for j, (dx, dy) in enumerate(spots):
        st = 2.9 + j * 0.32
        if t < st: continue
        with pop(c, CX + dx, PY + dy, (t - st) / 0.35):
            bubble(c, CX + dx, PY + dy, 260, 96, "bye bye", SAND, NAVY, 42, tail=-1 if dx > 0 else 1)

def sc_plant(c, t, d):
    ground(c, SAND)
    px_, py_ = CX + 80, GROUND + 30
    c.new_path(); c.move_to(px_ - 110, py_ - 150); c.line_to(px_ + 110, py_ - 150); c.line_to(px_ + 80, py_); c.line_to(px_ - 80, py_); c.close_path(); fill(c, TERRA)
    rrect(c, px_ - 125, py_ - 175, 250, 40, 10); fill(c, BROWN)
    g = ease((t - 1.0) / 6.5)
    stem = 40 + 430 * g
    line(c, px_, py_ - 170, px_, py_ - 170 - stem, 18, OLIVE)
    for i in range(int(1 + g * 6)):
        yy = py_ - 200 - i * 65
        if yy < py_ - 170 - stem + 20: break
        s = -1 if i % 2 else 1
        k = clamp(g * 6 - i)
        if k < 0.01: continue
        c.save(); c.translate(px_, yy); c.rotate(s * 0.6); c.scale(k, k)
        c.new_path(); c.move_to(0, 0); c.curve_to(s * 40, -50, s * 120, -40, s * 140, 0); c.curve_to(s * 110, 30, s * 40, 30, 0, 0); fill(c, TEAL)
        c.restore()
    if g > 0.85:
        for i in range(5):
            circle(c, px_ + math.cos(i * 1.26) * 60, py_ - 170 - stem + math.sin(i * 1.26) * 60, 38 * ease((g - 0.85) / 0.15), SAND)
        circle(c, px_, py_ - 170 - stem, 34, TERRA)
    # padre regando
    person(c, CX - 300, GROUND + 40, 600, NAVY, point=1, cap=CREAM)
    cx_, cy_ = CX - 165, PY + 480
    rrect(c, cx_ - 50, cy_ - 50, 120, 90, 18); fill(c, SKY)
    line(c, cx_ + 60, cy_ - 30, cx_ + 140, cy_ - 80, 16, SKY)
    for i in range(6):
        k = (t * 1.3 + i / 6) % 1
        circle(c, cx_ + 150 + k * 40, cy_ - 70 + k * 300, 9, TEAL, 1 - k)
    # niño junto a la planta
    person(c, CX + 320, GROUND + 40, 300, TERRA)

def mosque(c, x, base, s, col):
    rrect(c, x - 220 * s, base - 230 * s, 440 * s, 230 * s, 6); fill(c, col)
    c.new_path(); c.arc(x, base - 230 * s, 150 * s, math.pi, 2 * math.pi); fill(c, col)
    line(c, x, base - 380 * s, x, base - 430 * s, 8 * s, col)
    circle(c, x, base - 440 * s, 14 * s, SAND)
    for sx in (-1, 1):
        mx = x + sx * 300 * s
        rrect(c, mx - 32 * s, base - 520 * s, 64 * s, 520 * s, 8); fill(c, col)
        c.new_path(); c.move_to(mx - 40 * s, base - 520 * s); c.line_to(mx + 40 * s, base - 520 * s); c.line_to(mx, base - 610 * s); c.close_path(); fill(c, col)
        rrect(c, mx - 46 * s, base - 380 * s, 92 * s, 22 * s, 6); fill(c, col)
    for i in (-1, 0, 1):
        c.new_path(); ax = x + i * 120 * s
        c.move_to(ax - 36 * s, base); c.line_to(ax - 36 * s, base - 100 * s); c.arc(ax, base - 100 * s, 36 * s, math.pi, 2 * math.pi); c.line_to(ax + 36 * s, base); c.close_path(); fill(c, SAND, 0.9)

def sc_mosque(c, t, d):
    sun = ease(t / 2.5)
    sx, sy = CX, GROUND - 200 - 280 * sun
    glow = 0.5 + 0.5 * ease((t - 4.6) / 1.0)
    c.save(); c.translate(sx, sy); c.rotate(t * 0.15)
    for i in range(16):
        c.rotate(math.pi / 8)
        c.new_path(); c.move_to(0, -170); c.line_to(25, -360 - 60 * glow); c.line_to(-25, -360 - 60 * glow); c.close_path(); fill(c, SAND, 0.35 * glow)
    c.restore()
    circle(c, sx, sy, 160, SAND)
    ground(c, TEAL)
    rise = ease((t - 0.6) / 1.6)
    c.save(); c.rectangle(PX, PY, PW, GROUND - PY + 4); c.clip()
    mosque(c, CX, GROUND + 4 + 650 * (1 - rise), 1.0, NAVY)
    c.restore()
    if t > 4.6:
        for i in range(8):
            k = (t * 0.5 + i / 8) % 1
            star(c, PX + 80 + i * 115, PY + 120 + 60 * math.sin(i * 2.1), 18 * math.sin(k * math.pi), CREAM)

def sc_paths(c, t, d):
    ground(c, OLIVE)
    bx, by = CX, PY + PH - 60
    # dos caminos
    for s, col in ((-1, SAND), (1, GREY)):
        c.new_path(); c.move_to(bx - 70, by); c.curve_to(bx - 60, by - 300, bx + s * 300, by - 400, bx + s * 330, PY + 160)
        c.line_to(bx + s * 330 + 120, PY + 160); c.curve_to(bx + s * 300 + 120, by - 380, bx + 60, by - 280, bx + 70, by); c.close_path()
        fill(c, col)
    # señal: camino izquierdo = con beneficio, derecho = sin beneficio
    with pop(c, bx + 395, PY + 260, (t - 3.0) / 0.5):
        rrect(c, bx + 270, PY + 200, 260, 120, 20); fill(c, RED)
        line(c, bx + 340, PY + 230, bx + 460, PY + 290, 16, CREAM); line(c, bx + 340, PY + 290, bx + 460, PY + 230, 16, CREAM)
    with pop(c, bx - 265, PY + 260, (t - 3.5) / 0.5):
        circle(c, bx - 265, PY + 260, 70, TEAL)
        c.new_path(); c.set_line_width(16); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.move_to(bx - 300, PY + 262); c.line_to(bx - 275, PY + 290); c.line_to(bx - 228, PY + 232); c.set_source_rgb(*CREAM); c.stroke()
    # creyentes: grupo de figuras
    for i in range(3):
        with pop(c, CX - 130 + i * 130, GROUND + 130, (t - 0.2 - i * 0.25) / 0.5):
            person(c, CX - 130 + i * 130, GROUND + 140, 300, [TEAL, NAVY, TERRA][i], cap=CREAM)
    # pasos que se detienen ante el camino sin beneficio
    for i in range(5):
        k = clamp((t - 4.2 - i * 0.35) / 0.3)
        if k <= 0: continue
        x = bx + 30 + i * 50; y = by - 360 - i * 70
        c.save(); c.translate(x, y); c.rotate(0.6)
        c.new_path(); c.scale(1, 1.6); c.arc(0, 0, 14, 0, 2 * math.pi); c.restore(); fill(c, NAVY, 0.5 * k)
    if t > 6.4:
        k = ease((t - 6.4) / 0.4)
        rrect(c, bx + 150, by - 760, 320 * k, 34, 10); fill(c, RED)

def gear(c, x, y, r, teeth, ang, col):
    c.save(); c.translate(x, y); c.rotate(ang)
    c.new_path()
    for i in range(teeth * 2):
        a0 = i * math.pi / teeth; rr = r if i % 2 == 0 else r * 0.8
        c.arc(0, 0, rr, a0, a0 + math.pi / teeth)
    c.close_path(); fill(c, col)
    circle(c, 0, 0, r * 0.32, PANEL); c.restore()

def sc_industry(c, t, d):
    ground(c, SAND)
    # globo terráqueo
    with pop(c, CX + 220, PY + 330, t / 0.6):
        circle(c, CX + 220, PY + 330, 190, TEAL)
        c.save(); c.new_path(); c.arc(CX + 220, PY + 330, 190, 0, 2 * math.pi); c.clip()
        off = (t * 60) % 400
        for k in (-400, 0, 400):
            x = CX + 220 - 200 + off + k
            c.new_path(); c.move_to(x, PY + 250); c.curve_to(x + 80, PY + 180, x + 160, PY + 260, x + 120, PY + 360); c.curve_to(x + 60, PY + 420, x - 30, PY + 340, x, PY + 250); fill(c, OLIVE)
            c.new_path(); c.move_to(x + 220, PY + 380); c.curve_to(x + 280, PY + 330, x + 330, PY + 410, x + 290, PY + 470); c.curve_to(x + 250, PY + 500, x + 200, PY + 440, x + 220, PY + 380); fill(c, OLIVE)
        c.restore()
    # fábrica
    with pop(c, CX - 200, GROUND, (t - 0.4) / 0.6):
        fx = CX - 430
        rrect(c, fx, GROUND - 230, 480, 230, 0); fill(c, NAVY)
        c.new_path()
        for i in range(4):
            c.move_to(fx + i * 120, GROUND - 230); c.line_to(fx + i * 120 + 120, GROUND - 320); c.line_to(fx + i * 120 + 120, GROUND - 230)
        fill(c, NAVY)
        rrect(c, fx + 380, GROUND - 480, 60, 260, 6); fill(c, TERRA)
        for i in range(4):
            rrect(c, fx + 40 + i * 110, GROUND - 160, 60, 60, 8); fill(c, SAND)
        for i in range(4):
            k = (t * 0.5 + i / 4) % 1
            circle(c, fx + 410 + k * 80, GROUND - 500 - k * 220, 30 + k * 40, GREY, 0.7 * (1 - k))
    # engranajes
    gear(c, CX + 120, GROUND - 120, 110, 10, t * 1.2, TERRA)
    gear(c, CX + 300, GROUND - 40, 80, 8, -t * 1.65 + 0.2, SAND)
    gear(c, CX + 330, GROUND - 230, 60, 7, -t * 2.2, TEAL)

def sc_summit(c, t, d):
    c.new_path(); c.move_to(PX, GROUND + 60); c.line_to(CX - 40, PY + 300); c.line_to(PX + PW, GROUND + 60); c.close_path(); fill(c, TEAL)
    c.new_path(); c.move_to(CX - 40, PY + 300); c.line_to(CX - 150, PY + 470); c.line_to(CX - 90, PY + 440); c.line_to(CX - 40, PY + 490); c.line_to(CX + 20, PY + 430); c.line_to(CX + 70, PY + 450); c.close_path(); fill(c, CREAM)
    c.new_path(); c.move_to(PX - 40, GROUND + 160); c.line_to(PX + 200, PY + 620); c.line_to(PX + 480, GROUND + 160); c.close_path(); fill(c, OLIVE)
    ground(c, OLIVE)
    # figura subiendo
    u = ease_io(clamp((t - 0.8) / 3.0))
    x = lerp(CX + 360, CX - 40, u); y = lerp(GROUND + 30, PY + 300, u)
    person(c, x, y, 200, TERRA, wave=ease((t - 4.0) / 0.4), cap=CREAM)
    # bandera
    if t > 3.8:
        k = ease((t - 3.8) / 0.6)
        line(c, CX - 90, PY + 300, CX - 90, PY + 300 - 200 * k, 10, NAVY)
        c.new_path(); fx, fy = CX - 90, PY + 300 - 200 * k
        wv = 12 * math.sin(t * 5)
        c.move_to(fx, fy); c.curve_to(fx - 60, fy + wv, fx - 100, fy - wv, fx - 160 * k, fy + 10); c.line_to(fx - 160 * k, fy + 80); c.curve_to(fx - 100, fy + 70 - wv, fx - 60, fy + 70 + wv, fx, fy + 70); c.close_path(); fill(c, SAND)
        star(c, fx - 75 * k, fy + 38, 20 * k, TERRA)
    with pop(c, PX + PW - 150, PY + 150, (t - 1.0) / 0.5):
        circle(c, PX + PW - 150, PY + 150, 80, SAND)
        c.new_path(); c.set_line_width(18); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.move_to(PX + PW - 190, PY + 152); c.line_to(PX + PW - 160, PY + 185); c.line_to(PX + PW - 105, PY + 118); c.set_source_rgb(*NAVY); c.stroke()

SCENES = [
    (0.0, 7.0, sc_book, SKY), (7.0, 10.5, sc_proud, PANEL), (10.5, 16.8, sc_board, PANEL),
    (16.8, 24.1, sc_salam, SKY), (24.1, 27.0, sc_question, PANEL), (27.0, 35.8, sc_scale, SKY),
    (35.8, 38.5, sc_stairs, PANEL), (38.5, 44.0, sc_byebye, SKY), (44.0, 52.6, sc_plant, PANEL),
    (52.6, 61.3, sc_mosque, hx("F6E2C4")), (61.3, 69.1, sc_paths, SKY), (69.1, 77.3, sc_industry, PANEL),
    (77.3, SPEECH_END, sc_summit, SKY),
]

# ---------------------------------------------------------------- marca y textos
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
    text_c(c, "Sheij Muhammad ibn al-Uzaimín", W / 2, 285, 38, TEAL, a)
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
