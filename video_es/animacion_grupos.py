"""Animación flat vector «Los grupos de hoy» (1080x1920), subtítulos en español y marca de agua «Casa Antigua».

Uso: python3 animacion_flat.py <video_o_audio_original> <salida.mp4> [segundo_preview]
"""
import math, subprocess, sys
import cairo

SRC = sys.argv[1]
OUT = sys.argv[2]
PREVIEW = float(sys.argv[3]) if len(sys.argv) > 3 else None
W, H, FPS = 1080, 1920, 30
SPEECH_END = 97.9
END_CARD = 4.0
TOTAL = SPEECH_END + END_CARD

def hx(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) / 255 for i in (0, 2, 4))

BG = hx("F4EBDD"); PANEL = hx("FBF6EE"); NAVY = hx("1F3A4D"); TEAL = hx("2A7F7A")
TERRA = hx("C8603C"); SAND = hx("E3B964"); OLIVE = hx("7E8B4F"); CREAM = hx("FFFDF8")
SKY = hx("CFE3E0"); RED = hx("D2453A"); BROWN = hx("8A5A3B"); GREY = hx("B9B2A6")
SKIN = hx("D9A47E")

SUBS = [
(0.0,2.5,"Las mayores convocatorias de hoy son *Jama'at* *at-Tabligh* y los *Hermanos* *Musulmanes*."),
(2.5,4.0,"Esta la fundó *Muhammad* *Ilyas*,"),
(4.0,5.5,"y aquella la fundó *Hasan* *al-Banna*."),
(5.5,7.0,"¿Quién es Muhammad Ilyas?"),
(7.0,8.0,"Muhammad Ilyas es de la *India*."),
(8.0,12.0,"En el año *1343*, hace cien años, vino e hizo el *Hajj*."),
(12.0,13.0,"Tras el Hajj, fue a *Medina*."),
(13.0,15.5,"Y al llegar a Medina, *durmió* en la Mezquita del Profeta."),
(15.5,17.5,"Y cuando durmió, dice que *vio* al Profeta (la paz sea con él)"),
(17.5,21.5,"y que el Profeta le dijo: «tres días, *cuarenta* días y *cuatro* *meses*»."),
(21.5,23.5,"Entonces fue a su pueblo, los *mewatíes* (una comunidad musulmana de Mewat, India),"),
(23.5,25.0,"los *llamó*, y se convirtió en una da'wa (una convocatoria que él fundó)."),
(25.0,28.5,"Una da'wa fundada sobre un *sueño* indio."),
(28.5,29.5,"Y se *extendió*."),
(29.5,32.5,"Y él es *chishtí*, *suhrawardí*, *qadirí*, *naqshbandí*:"),
(32.5,33.5,"cuatro *tariqas* *sufíes* (órdenes del sufismo)."),
(33.5,36.0,"Sé que algunos de ustedes no saben qué son."),
(36.0,38.5,"Y solía quedarse retirado en la *cúpula* de su sheij en la *tumba*,"),
(38.5,42.0,"Rashid al-Kanhuki, y permanecía allí *días*."),
(42.0,43.5,"Y el día que murió, lo enterraron en la *mezquita*:"),
(43.5,45.0,"a él, a su esposa y a su hijo."),
(45.0,47.0,"Y el último de sus predicadores, *In'am* *al-Hasan*,"),
(47.0,49.5,"lo enterraron en la Mezquita *Nizam* *ad-Din*, dentro de la mezquita."),
(49.5,52.5,"Este es el *fundador* de Jama'at at-Tabligh:"),
(52.5,55.0,"adoradores de *tumbas*, *sufíes*, intérpretes de los *Atributos*,"),
(55.0,57.5,"*maturidíes*, *deobandíes*."),
(57.5,60.5,"Cuando se te advierte de ellos, ¿por qué te *enojas*?"),
(60.5,63.5,"En cuanto a *Hasan* *al-Banna*, sobre sí mismo, en sus memorias y en sus tres charlas,"),
(63.5,65.5,"aclara que es *husafí* (orden sufí)."),
(65.5,67.5,"Y la Hasafiyya es una rama de la *Shadhiliyya*."),
(67.5,70.5,"Y que solía quedarse retirado en la *cúpula* de Sinjar,"),
(70.5,74.5,"y solía repetir el pedir *auxilio* al Profeta (la paz sea con él) el día del *Mawlid*."),
(74.5,77.5,"Y es un *ash'arí* *mufawwid*; lo menciona de sí mismo en sus escritos."),
(77.5,79.5,"Si se te *advierte* de estos grupos,"),
(79.5,81.5,"que son los mayores grupos de hoy,"),
(81.5,83.0,"sus *fundadores* están sobre esto:"),
(83.0,85.5,"culto a las *tumbas*, *sufismo* e interpretación de los *Atributos*."),
(85.5,86.5,"¿Eres adorador de tumbas?"),
(86.5,87.0,"*No*."),
(87.0,87.5,"¿Eres sufí?"),
(87.5,88.0,"*No*."),
(88.0,89.5,"¿Eres ash'arí que interpreta los Atributos?"),
(89.5,90.0,"*No*."),
(90.0,92.5,"Entonces, ¿por qué te *enojas* por estos grupos y organizaciones?"),
(92.5,94.0,"Se dijo: «¿Quién es el *sunní*?»."),
(94.0,96.5,"Dijo: «Aquel que, cuando se menciona a alguien de la gente de las *pasiones* y las *innovaciones*,"),
(96.5,SPEECH_END,"*no* *se* *enoja* por eso»."),
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

SPEAKER = "Sheij Abu Zakariyya al-Hudaydi"

GOLD_ = hx("C9A060"); GLOW = hx("FFE7A8"); DKGREEN = hx("2F6B4A"); GREEN = hx("3E8E5E"); NIGHT = hx("223B55")

def star(c, x, y, r, col, a=1.0):
    if r <= 0: return
    c.new_path()
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.42
        ang = -math.pi / 2 + i * math.pi / 5
        (c.move_to if i == 0 else c.line_to)(x + math.cos(ang) * rr, y + math.sin(ang) * rr)
    c.close_path(); fill(c, col, a)

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

def sky(c, top, bottom):
    g = cairo.LinearGradient(0, PY, 0, GROUND)
    g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(1, *bottom)
    c.rectangle(PX, PY, PW, PH); c.set_source(g); c.fill()

def dome_building(c, x, base, s, col, dome=None):
    dome = dome or col
    rrect(c, x - 120 * s, base - 160 * s, 240 * s, 160 * s, 4); fill(c, col)
    c.new_path(); c.arc(x, base - 160 * s, 100 * s, math.pi, 2 * math.pi); fill(c, dome)
    line(c, x, base - 260 * s, x, base - 300 * s, 6 * s, GOLD_)
    c.new_path(); c.move_to(x - 30 * s, base); c.line_to(x - 30 * s, base - 70 * s); c.arc(x, base - 70 * s, 30 * s, math.pi, 2 * math.pi); c.line_to(x + 30 * s, base); c.close_path(); fill(c, NAVY)

def grave(c, x, base, s=1.0, col=GREY):
    rrect(c, x - 70 * s, base - 30 * s, 140 * s, 30 * s, 8); fill(c, col)
    rrect(c, x - 14 * s, base - 110 * s, 28 * s, 90 * s, 10); fill(c, col)

def card(c, x, y, w, h, k, col=CREAM):
    rrect(c, x + 8, y + 10, w, h, 28); fill(c, NAVY, 0.12 * k)
    rrect(c, x, y, w, h, 28); fill(c, col, k)

def bullet_list(c, items, T, x, y, step=92, size=40, mark="x"):
    for i, (st, txt) in enumerate(items):
        if T < st: continue
        k = ease((T - st) / 0.4)
        yy = y + i * step
        if mark == "x": cross(c, x, yy - 12, 28, (T - st) / 0.4)
        else: check(c, x, yy - 12, 28, (T - st) / 0.4)
        font(c, size, True); c.move_to(x + 50, yy); c.set_source_rgba(*NAVY, k); c.show_text(txt)

def tent(c, x, base, w, col, label, k):
    with pop(c, x, base - 120, k):
        c.new_path(); c.move_to(x - w / 2, base); c.line_to(x, base - 260); c.line_to(x + w / 2, base); c.close_path(); fill(c, col)
        c.new_path(); c.move_to(x - 40, base); c.line_to(x, base - 130); c.line_to(x + 40, base); c.close_path(); fill(c, NAVY, 0.6)
        line(c, x, base - 260, x, base - 330, 6, NAVY); c.new_path(); c.move_to(x, base - 330); c.line_to(x + 70, base - 310); c.line_to(x, base - 290); c.close_path(); fill(c, SAND)
    tag(c, x, base + 60, label, NAVY, CREAM, 30, ease(k))

# ------------------------------------------------ escenas
def sc_groups(c, t, d):
    T = t
    sky(c, hx("E6EEF0"), hx("F4EBDD")); ground(c, SAND)
    tent(c, CX - 230, GROUND + 10, 360, TEAL, "Jama'at at-Tabligh", T / 0.6)
    tent(c, CX + 230, GROUND + 10, 360, TERRA, "Hermanos Musulmanes", (T - 0.6) / 0.6)
    tag(c, CX, PY + 110, "Las mayores convocatorias de hoy", NAVY, CREAM, 36, ease(T / 0.5))
    if T > 2.5: tag(c, CX - 230, PY + 230, "Fundador: Muhammad Ilyas", TEAL, CREAM, 28, ease((T - 2.5) / 0.4))
    if T > 4.0: tag(c, CX + 230, PY + 300, "Fundador: Hasan al-Banna", TERRA, CREAM, 28, ease((T - 4.0) / 0.4))
    if T > 5.5: text_c(c, "?", CX - 230, GROUND - 330 + 10 * math.sin(T * 5), 120, TERRA, ease((T - 5.5) / 0.3))

def ship(c, x, y, s):
    c.new_path(); c.move_to(x - 70 * s, y); c.line_to(x + 70 * s, y); c.line_to(x + 50 * s, y + 30 * s); c.line_to(x - 50 * s, y + 30 * s); c.close_path(); fill(c, BROWN)
    line(c, x, y, x, y - 80 * s, 5 * s, NAVY)
    c.new_path(); c.move_to(x + 4 * s, y - 76 * s); c.line_to(x + 50 * s, y - 20 * s); c.line_to(x + 4 * s, y - 20 * s); c.close_path(); fill(c, CREAM)

def kaaba(c, x, base, s):
    rrect(c, x - 60 * s, base - 120 * s, 120 * s, 120 * s, 4); fill(c, hx("1B1B1B"))
    rrect(c, x - 60 * s, base - 95 * s, 120 * s, 16 * s, 2); fill(c, GOLD_)

def sc_journey(c, t, d):
    T = t + 7.0
    sky(c, hx("CFE3E0"), hx("E6F0EC"))
    rrect(c, PX, CY + 80, PW, PY + PH - CY - 80, 0); fill(c, hx("9CC7C2"))
    # India (derecha) → Hiyaz (izquierda)
    c.new_path(); c.move_to(PX + PW - 300, CY + 80); c.curve_to(PX + PW - 260, CY - 120, PX + PW - 120, CY - 140, PX + PW, CY - 100); c.line_to(PX + PW, CY + 80); c.close_path(); fill(c, OLIVE)
    c.new_path(); c.move_to(PX, CY - 80); c.curve_to(PX + 120, CY - 140, PX + 260, CY - 90, PX + 300, CY + 80); c.line_to(PX, CY + 80); c.close_path(); fill(c, SAND)
    tag(c, PX + PW - 160, CY - 190, "India", OLIVE, CREAM, 32, 1)
    tag(c, PX + 150, CY - 190, "Hiyaz", BROWN, CREAM, 32, 1)
    kaaba(c, PX + 150, CY + 60, 0.9)
    u = ease_io(clamp((T - 8.0) / 3.5))
    sx = lerp(PX + PW - 280, PX + 330, u); sy = CY + 150 + math.sin(u * math.pi) * 60
    c.new_path(); c.set_dash([16, 14]); c.move_to(PX + PW - 280, CY + 150)
    c.curve_to(PX + PW - 450, CY + 210, PX + 500, CY + 210, sx, sy); c.set_line_width(5); c.set_source_rgba(*NAVY, 0.6); c.stroke(); c.set_dash([])
    ship(c, sx, sy - 20, 1.0)
    if T > 7.0: person(c, PX + PW - 160, CY + 70, 150, TEAL, cap=CREAM)
    if T > 8.0:
        with pop(c, CX, PY + 140, (T - 8.0) / 0.5):
            rrect(c, CX - 190, PY + 70, 380, 140, 24); fill(c, CREAM)
            text_c(c, "Año 1343 H", CX, PY + 135, 46, NAVY)
            text_c(c, "hace unos 100 años", CX, PY + 185, 28, TEAL, bold=False)
    if T > 11.0: tag(c, PX + 150, CY - 270, "Hajj", GOLD_, CREAM, 32, ease((T - 11.0) / 0.4))

def sc_dream(c, t, d):
    T = t + 12.0
    sky(c, NIGHT, hx("35557A"))
    for i in range(18):
        k = (T * 0.4 + i * 0.37) % 1
        star(c, PX + 40 + (i * 157) % (PW - 80), PY + 60 + (i * 89) % 330, 9 * (0.4 + 0.6 * math.sin(k * math.pi)), CREAM, 0.9)
    ground(c, hx("1A2B40")); rrect(c, PX, GROUND, PW, PY + PH - GROUND, 0); fill(c, hx("1A2B40"))
    # Mezquita del Profeta (silueta)
    c.new_path(); c.arc(CX - 200, GROUND - 200, 110, math.pi, 2 * math.pi); fill(c, GREEN)
    rrect(c, CX - 380, GROUND - 200, 360, 200, 4); fill(c, hx("2C4560"))
    for sx in (CX - 420, CX + 20):
        rrect(c, sx - 22, GROUND - 420, 44, 420, 6); fill(c, hx("2C4560"))
        c.new_path(); c.move_to(sx - 28, GROUND - 420); c.line_to(sx + 28, GROUND - 420); c.line_to(sx, GROUND - 480); c.close_path(); fill(c, hx("2C4560"))
    tag(c, CX - 200, PY + 110, "Medina", GREEN, CREAM, 34, ease((T - 12.0) / 0.4))
    # durmiendo
    if T > 13.0:
        k = ease((T - 13.0) / 0.5)
        rrect(c, CX + 120, GROUND - 60, 280, 50, 25); fill(c, TEAL, k)
        circle(c, CX + 110, GROUND - 60, 36, SKIN, k)
        c.new_path(); c.arc(CX + 110, GROUND - 66, 37, math.pi, 2 * math.pi); fill(c, CREAM, k)
        for i in range(3):
            z = (T * 0.6 + i / 3) % 1
            text_c(c, "z", CX + 150 + i * 30 + z * 40, GROUND - 120 - z * 120, 30 + i * 8, CREAM, k * (1 - z))
    # nube del sueño: solo texto (no se representa al Profeta ﷺ)
    if T > 15.5:
        k = (T - 15.5) / 0.6
        with pop(c, CX + 220, PY + 330, k):
            for dx, dy, r in ((-150, 20, 90), (-60, -40, 120), (70, -30, 110), (160, 30, 80), (0, 50, 110)):
                circle(c, CX + 220 + dx, PY + 330 + dy, r, CREAM, 0.95)
            text_c(c, "«Dice que vio…»", CX + 220, PY + 300, 34, NAVY)
            if T > 17.5:
                text_c(c, "3 días · 40 días", CX + 220, PY + 350, 38, TERRA)
                text_c(c, "4 meses", CX + 220, PY + 395, 38, TERRA)
        for i in range(3):
            circle(c, CX + 160 - i * 16, GROUND - 150 - i * 60, 12 + i * 6, CREAM, 0.9 * ease(k))

def sc_mewat(c, t, d):
    T = t + 21.5
    sky(c, hx("F3D9B1"), hx("F8E8CF")); ground(c, SAND)
    for i in range(4):
        dome_building(c, PX + 140 + i * 230, GROUND + 10, 0.55, hx("E3C59A"), hx("D8B080"))
    tag(c, CX, PY + 110, "Los mewatíes · Mewat, India", OLIVE, CREAM, 34, ease((T - 21.5) / 0.4))
    person(c, CX - 300, GROUND + 50, 360, TEAL, cap=CREAM, wave=ease((T - 23.5) / 0.4))
    n = int(clamp((T - 23.5) / 4.0) * 12)
    for i in range(n):
        x = CX - 120 + (i % 6) * 90; y = GROUND + 60 + (i // 6) * 50
        person(c, x, y, 200, [OLIVE, TERRA, NAVY, BROWN][i % 4], cap=CREAM)
    if T > 25.0:
        with pop(c, CX + 200, PY + 260, (T - 25.0) / 0.5):
            for dx, dy, r in ((-130, 10, 70), (-40, -30, 95), (70, -20, 85), (150, 20, 60)):
                circle(c, CX + 200 + dx, PY + 260 + dy, r, CREAM, 0.95)
            text_c(c, "Fundada sobre", CX + 200, PY + 250, 32, NAVY)
            text_c(c, "un sueño", CX + 200, PY + 292, 32, TERRA)
    if T > 28.5:
        for i in range(14):
            k = ((T - 28.5) * 0.8 + i / 14) % 1
            circle(c, CX + math.cos(i * 0.45) * 450 * k, PY + 520 + math.sin(i * 0.45) * 200 * k, 10, TEAL, 1 - k)
        tag(c, CX, PY + 400, "Se extendió", TEAL, CREAM, 34, ease((T - 28.5) / 0.4))

def sc_tariqas(c, t, d):
    T = t + 29.5
    sky(c, hx("EDE6F2"), hx("F6F0EA"))
    names = [("Chishtí", TEAL), ("Suhrawardí", TERRA), ("Qadirí", OLIVE), ("Naqshbandí", NAVY)]
    for i, (nm, col) in enumerate(names):
        k = (T - 29.6 - i * 0.6) / 0.4
        x = CX - 220 + (i % 2) * 440; y = PY + 300 + (i // 2) * 280
        with pop(c, x, y, k):
            circle(c, x, y, 110, col); circle(c, x, y, 90, CREAM, 0.15)
            text_c(c, nm, x, y + 12, 36, CREAM)
    if T > 32.5:
        k = ease((T - 32.5) / 0.4)
        rrect(c, CX - 300, PY + 780, 600, 100, 50); fill(c, GOLD_, k)
        text_c(c, "4 órdenes sufíes (tariqas)", CX, PY + 843, 38, CREAM, k)

def sc_tombs(c, t, d):
    T = t + 36.0
    sky(c, hx("E6E0D6"), hx("F4EEE4")); ground(c, SAND)
    if T < 42.0:
        dome_building(c, CX - 120, GROUND + 10, 1.4, hx("D9CFC0"), hx("B9B2A6"))
        grave(c, CX - 120, GROUND + 10, 1.0)
        tag(c, CX - 120, PY + 110, "Cúpula sobre la tumba de su sheij", NAVY, CREAM, 32, ease((T - 36.0) / 0.4))
        person(c, CX + 260, GROUND + 50, 330, TEAL, cap=CREAM)
        if T > 38.5:
            tag(c, CX - 120, PY + 210, "Rashid al-Kanhuki", BROWN, CREAM, 32, ease((T - 38.5) / 0.4))
            n = int((T - 38.5) * 2) + 1
            with pop(c, CX + 260, PY + 320, (T - 38.5) / 0.4):
                rrect(c, CX + 160, PY + 260, 200, 120, 18); fill(c, CREAM)
                text_c(c, f"Día {n}", CX + 260, PY + 335, 40, TERRA)
    else:
        # mezquita con tumbas dentro
        rrect(c, PX + 80, GROUND - 420, PW - 160, 420, 10); fill(c, hx("E9DFCF"))
        c.new_path(); c.arc(CX, GROUND - 420, 160, math.pi, 2 * math.pi); fill(c, hx("CFC2AC"))
        tag(c, CX, PY + 110, "Enterrado dentro de la mezquita", NAVY, CREAM, 32, 1)
        labels = ["Él", "Su esposa", "Su hijo"]
        for i in range(3):
            st = 42.0 if i == 0 else 43.5 + (i - 1) * 0.4
            if T < st: continue
            x = CX - 260 + i * 260
            with pop(c, x, GROUND - 40, (T - st) / 0.4):
                grave(c, x, GROUND - 10, 1.1)
            tag(c, x, GROUND + 50, labels[i], GREY, NAVY, 28, ease((T - st) / 0.4))
        if T > 45.0:
            k = ease((T - 45.0) / 0.4)
            rrect(c, CX - 330, GROUND - 380, 660, 130, 24); fill(c, NAVY, k)
            text_c(c, "Y el último: In'am al-Hasan", CX, GROUND - 322, 34, CREAM, k)
            if T > 47.0: text_c(c, "Mezquita Nizam ad-Din", CX, GROUND - 275, 30, SAND, ease((T - 47.0) / 0.4))

def sc_summary_tabligh(c, t, d):
    T = t + 49.5
    sky(c, hx("F3E6D2"), hx("FBF6EE"))
    card(c, PX + 60, PY + 60, PW - 120, 620, 1)
    tag(c, CX, PY + 60, "El fundador de Jama'at at-Tabligh", TEAL, CREAM, 34, 1)
    items = [(52.5, "Culto a las tumbas"), (53.3, "Sufismo"), (54.0, "Interpretación de los Atributos"), (55.0, "Maturidí"), (55.8, "Deobandí")]
    bullet_list(c, items, T, PX + 130, PY + 190, 100, 38)
    if T > 57.5:
        k = ease((T - 57.5) / 0.4)
        person(c, CX, GROUND + 60, 300, TERRA, cap=CREAM, chest=1.1)
        for i in range(3):
            z = (T * 1.2 + i / 3) % 1
            circle(c, CX - 40 + i * 40, GROUND - 330 - z * 80, 14 + z * 14, GREY, (1 - z) * k)
        with pop(c, CX + 230, GROUND - 330, (T - 57.7) / 0.4):
            bubble(c, CX + 230, GROUND - 330, 380, 100, "¿Por qué te enojas?", NAVY, CREAM, 34, tail=-1)

def sc_banna(c, t, d):
    T = t + 60.5
    sky(c, hx("F3E6D2"), hx("FBF6EE"))
    card(c, PX + 60, PY + 60, PW - 120, 760, 1)
    tag(c, CX, PY + 60, "Hasan al-Banna, sobre sí mismo", TERRA, CREAM, 34, 1)
    # libros: memorias y tres charlas
    for i, (lab, col) in enumerate((("Memorias", BROWN), ("Tres charlas", OLIVE))):
        k = (T - 60.7 - i * 0.4) / 0.4
        x = CX - 150 + i * 300
        with pop(c, x, PY + 230, k):
            rrect(c, x - 110, PY + 150, 220, 150, 14); fill(c, col)
            rrect(c, x - 96, PY + 164, 192, 122, 10); fill(c, CREAM)
            text_c(c, lab, x, PY + 236, 30, NAVY)
    items = [(63.5, "Husafí (orden sufí)"), (65.5, "Rama de la Shadhiliyya"), (67.5, "Retiro en la cúpula de Sinjar"),
             (70.5, "Pedía auxilio al Profeta en el Mawlid"), (74.5, "Ash'arí mufawwid")]
    bullet_list(c, items, T, PX + 120, PY + 380, 86, 34)

QA = [(85.5, "¿Eres adorador de tumbas?", 86.5), (87.0, "¿Eres sufí?", 87.5), (88.0, "¿Eres ash'arí que interpreta los Atributos?", 89.5)]
def sc_question(c, t, d):
    T = t + 77.5
    sky(c, hx("E6EEF0"), hx("F4EBDD")); ground(c, SAND)
    if T < 85.5:
        tag(c, CX, PY + 110, "Los mayores grupos de hoy", NAVY, CREAM, 36, ease((T - 79.5) / 0.4))
        tent(c, CX - 230, GROUND + 10, 300, TEAL, "Tabligh", 1)
        tent(c, CX + 230, GROUND + 10, 300, TERRA, "Hermanos Musulmanes", 1)
        if T > 81.5:
            k = ease((T - 81.5) / 0.4)
            rrect(c, CX - 340, PY + 180, 680, 210, 24); fill(c, CREAM, k)
            text_c(c, "Sus fundadores:", CX, PY + 230, 32, TEAL, k)
            if T > 83.0:
                text_c(c, "tumbas · sufismo ·", CX, PY + 290, 36, TERRA, ease((T - 83.0) / 0.4))
                text_c(c, "interpretar los Atributos", CX, PY + 340, 36, TERRA, ease((T - 83.4) / 0.4))
    else:
        person(c, CX - 260, GROUND + 50, 380, TEAL, cap=CREAM)
        tag(c, CX - 260, GROUND + 100, "Tú", NAVY, CREAM, 30, 1)
        for i, (st, q, ans) in enumerate(QA):
            if T < st: continue
            y = PY + 130 + i * 150
            k = ease((T - st) / 0.3)
            rrect(c, CX - 380, y - 50, 640, 100, 30); fill(c, CREAM, k)
            font(c, 30 if len(q) < 30 else 25, True); c.move_to(CX - 350, y + 10); c.set_source_rgba(*NAVY, k); c.show_text(q)
            if T > ans:
                tag(c, CX + 340, y, "No", RED, CREAM, 36, ease((T - ans) / 0.3))
        if T > 90.0:
            k = (T - 90.0) / 0.4
            with pop(c, CX + 120, GROUND - 200, k):
                bubble(c, CX + 120, GROUND - 200, 560, 130, "¿Entonces por qué te enojas?", TERRA, CREAM, 36, tail=-1)

def sc_sunni(c, t, d):
    T = t + 92.5
    sky(c, hx("CFE3E0"), hx("EAF3EE")); ground(c, OLIVE)
    with pop(c, CX, PY + 220, (T - 92.5) / 0.5):
        rrect(c, CX - 300, PY + 140, 600, 150, 30); fill(c, CREAM)
        text_c(c, "«¿Quién es el sunní?»", CX, PY + 232, 46, NAVY)
    if T > 94.0:
        k = ease((T - 94.0) / 0.5)
        rrect(c, PX + 80, PY + 310, PW - 160, 250, 30); fill(c, NAVY, k)
        text_c(c, "El que, al mencionarse a alguien", CX, PY + 380, 34, CREAM, k)
        text_c(c, "de la gente de pasiones e innovaciones,", CX, PY + 430, 34, CREAM, k)
        if T > 96.5: text_c(c, "no se enoja por eso.", CX, PY + 505, 42, SAND, ease((T - 96.5) / 0.4))
    person(c, CX, GROUND + 60, 250, TEAL, cap=CREAM)
    if T > 96.7: check(c, CX + 170, GROUND - 160, 46, (T - 96.7) / 0.4)

SCENES = [
    (0.0, 7.0, sc_groups, PANEL), (7.0, 12.0, sc_journey, PANEL), (12.0, 21.5, sc_dream, PANEL),
    (21.5, 29.5, sc_mewat, PANEL), (29.5, 36.0, sc_tariqas, PANEL), (36.0, 49.5, sc_tombs, PANEL),
    (49.5, 60.5, sc_summary_tabligh, PANEL), (60.5, 77.5, sc_banna, PANEL), (77.5, 92.5, sc_question, PANEL),
    (92.5, SPEECH_END, sc_sunni, PANEL),
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
