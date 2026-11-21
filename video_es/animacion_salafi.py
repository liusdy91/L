"""Animación flat vector «¿Por qué salafí?» (1080x1920), subtítulos en español y marca de agua «Casa Antigua».

Uso: python3 animacion_flat.py <video_o_audio_original> <salida.mp4> [segundo_preview]
"""
import math, subprocess, sys
import cairo

SRC = sys.argv[1]
OUT = sys.argv[2]
PREVIEW = float(sys.argv[3]) if len(sys.argv) > 3 else None
W, H, FPS = 1080, 1920, 30
SPEECH_END = 58.6
END_CARD = 4.0
TOTAL = SPEECH_END + END_CARD

def hx(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) / 255 for i in (0, 2, 4))

BG = hx("F4EBDD"); PANEL = hx("FBF6EE"); NAVY = hx("1F3A4D"); TEAL = hx("2A7F7A")
TERRA = hx("C8603C"); SAND = hx("E3B964"); OLIVE = hx("7E8B4F"); CREAM = hx("FFFDF8")
SKY = hx("CFE3E0"); RED = hx("D2453A"); BROWN = hx("8A5A3B"); GREY = hx("B9B2A6")
SKIN = hx("D9A47E")

SUBS = [
(0.0,1.0,"¿Pero por qué *salafí*?"),
(1.0,4.5,"Porque si dices «soy *musulmán*», el *takfirí* también dice «soy musulmán»,"),
(4.5,7.5,"y el *yahmí* dice «soy musulmán». Así que tú dices: «¡Soy *salafí*!»."),
(7.5,13.0,"Es decir: no sigo a todas esas *sectas*; sigo a los *Compañeros* del Mensajero de Allah"),
(13.0,14.5,"(la paz sea con él)."),
(14.5,17.5,"Estoy sobre la *creencia* de los Compañeros del Mensajero de Allah (la paz sea con él)."),
(17.5,21.5,"Estoy sobre el *método* de los Compañeros del Mensajero de Allah (la paz sea con él)."),
(21.5,27.0,"Así que decir esto, cuando las cosas se *confunden*, es algo *necesario*."),
(27.0,28.5,"Y en esto están los *imames* del Islam."),
(28.5,35.0,"El Sheij al-Islam *Ibn* *Taymiyyah* mencionó que no hay *reproche* en que alguien se atribuya a los Salaf."),
(35.0,39.0,"Nuestros imames y sabios —el Sheij *Ibn* *Baz* (que Allah tenga misericordia de él),"),
(39.0,43.0,"el Sheij *Ibn* *Uzaimín* (que Allah tenga misericordia de él) y el Sheij *Salih* *al-Fawzán* (que Allah lo proteja)—"),
(43.0,49.0,"todos afirmaron que atribuirse a los Salaf es algo *bueno* y *loable*."),
(49.0,SPEECH_END,"De hecho, el Sheij Ibn Uzaimín (que Allah tenga misericordia de él) mencionó que es *obligatorio* en cuanto a *seguirlos*."),
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

SPEAKER = "¿Por qué salafí?"

GOLD_ = hx("C9A060"); GLOW = hx("FFE7A8"); DKGREEN = hx("2F6B4A")

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

# ------------------------------------------------ escenas
def sc_muslim(c, t, d):
    """Todos dicen «soy musulmán» → tú dices «¡soy salafí!»"""
    T = t
    sky(c, hx("E6EEF0"), hx("F4EBDD")); ground(c, SAND)
    figs = [(CX - 300, TEAL, 1.0, "Tú"), (CX, hx("8C8C8C"), 2.4, "Takfirí"), (CX + 300, hx("9A8F84"), 4.6, "Yahmí")]
    salafi = T > 5.8
    for i, (x, col, st, lab) in enumerate(figs):
        k = (T - st + 0.6) / 0.5
        if k <= 0: continue
        dim = 0.45 if (salafi and i > 0) else 1.0
        with pop(c, x, GROUND + 40, k, a=dim):
            person(c, x, GROUND + 40, 360, col, cap=CREAM)
        tag(c, x, GROUND + 100, lab, NAVY if i == 0 else GREY, CREAM, 30, ease(k) * dim)
        if T > st:
            if i == 0 and salafi:
                with pop(c, x + 20, PY + 300, (T - 5.8) / 0.4):
                    bubble(c, x + 20, PY + 300, 290, 110, "¡Soy salafí!", GOLD_, CREAM, 44, tail=1)
            else:
                with pop(c, x + 10, PY + 300 + (i % 2) * 120, (T - st) / 0.4, a=dim):
                    bubble(c, x + 10, PY + 300 + (i % 2) * 120, 290, 100, "Soy musulmán", CREAM, NAVY, 36, tail=1)
    # signos de interrogación: todo se confunde
    if 4.6 < T < 6.0:
        for i in range(3):
            text_c(c, "?", CX - 200 + i * 200, PY + 130 + 20 * math.sin(T * 6 + i), 90, TERRA, ease((T - 4.6) / 0.4))
    if salafi: check(c, CX - 300, PY + 150, 50, (T - 6.0) / 0.4)

def signpost(c, x, base, txt, col, ang, a=1.0):
    line(c, x, base, x, base - 330, 14, BROWN, a)
    c.save(); c.translate(x, base - 290); c.rotate(ang)
    rrect(c, -10, -38, 260, 76, 14); fill(c, col, a)
    font(c, 30, True); c.move_to(20, 11); c.set_source_rgba(*CREAM, a); c.show_text(txt)
    c.restore()

def sc_path(c, t, d):
    """No sigo esas sectas: sigo a los Compañeros."""
    T = t + 7.5
    sky(c, hx("F6E2C4"), hx("FBF1E0")); ground(c, OLIVE)
    # camino iluminado hacia la puerta
    c.new_path(); c.move_to(CX - 70, GROUND - 120); c.line_to(CX + 70, GROUND - 120); c.line_to(CX + 360, PY + PH); c.line_to(CX - 360, PY + PH); c.close_path(); fill(c, hx("E9D3A8"))
    ga = ease((T - 9.5) / 1.0)
    for i in range(12):
        a = i * math.pi / 6 + T * 0.2
        line(c, CX, GROUND - 250, CX + math.cos(a) * 220, GROUND - 250 + math.sin(a) * 220, 10, GLOW, 0.5 * ga)
    c.new_path(); w, h = 200, 300; x, base = CX, GROUND - 118
    c.move_to(x - w / 2, base); c.line_to(x - w / 2, base - h + w / 2); c.arc(x, base - h + w / 2, w / 2, math.pi, 2 * math.pi); c.line_to(x + w / 2, base); c.close_path(); fill(c, GOLD_, 0.4 + 0.6 * ga)
    c.new_path(); w2 = 150
    c.move_to(x - w2 / 2, base); c.line_to(x - w2 / 2, base - h + 40 + w2 / 2); c.arc(x, base - h + 40 + w2 / 2, w2 / 2, math.pi, 2 * math.pi); c.line_to(x + w2 / 2, base); c.close_path(); fill(c, GLOW, 0.5 + 0.5 * ga)
    tag(c, CX, PY + 110, "Los Compañeros del Mensajero", DKGREEN, CREAM, 36, ga)
    # carteles de las sectas, tachados
    for i, (sx, ang) in enumerate(((PX + 90, -0.15), (PX + 120, 0.2), (PX + PW - 340, -0.2), (PX + PW - 320, 0.15))):
        k = ease((T - 7.7 - i * 0.25) / 0.4)
        signpost(c, sx, GROUND + 30 + (i % 2) * 60, "Secta", GREY, ang, k)
        bse = GROUND + 30 + (i % 2) * 60
        if T > 8.8 + i * 0.2: cross(c, sx + math.cos(ang) * 200, bse - 290 + math.sin(ang) * 200, 30, (T - 8.8 - i * 0.2) / 0.3)
    # caminante de espaldas hacia la puerta
    u = ease((T - 9.0) / 5.0)
    bob = abs(math.sin(T * 7)) * 8
    person(c, CX, lerp(GROUND + 150, GROUND + 60, u) - bob, lerp(380, 300, u), TEAL, cap=CREAM)

def pillar(c, x, base, h, w, col, label, icon, k):
    hh = h * ease(k)
    if hh < 2: return
    rrect(c, x - w / 2, base - hh, w, hh, 8); fill(c, col)
    rrect(c, x - w / 2 - 20, base - hh - 24, w + 40, 28, 8); fill(c, BROWN)
    rrect(c, x - w / 2 - 20, base - 20, w + 40, 24, 8); fill(c, BROWN)
    for i in range(3): rrect(c, x - w / 2 + 18 + i * (w - 36) / 3, base - hh + 30, 14, hh - 60, 7); fill(c, CREAM, 0.25)
    if k > 0.6:
        a = ease((k - 0.6) / 0.4)
        circle(c, x, base - hh / 2, 64, CREAM, a)
        icon(c, x, base - hh / 2, a)
        tag(c, x, base + 60, label, NAVY, CREAM, 34, a)

def icon_heart(c, x, y, a):
    c.new_path(); s = 30
    c.move_to(x, y + s * 0.9); c.curve_to(x - s * 1.4, y - s * 0.1, x - s * 0.7, y - s * 1.1, x, y - s * 0.45)
    c.curve_to(x + s * 0.7, y - s * 1.1, x + s * 1.4, y - s * 0.1, x, y + s * 0.9); c.close_path(); fill(c, TERRA, a)

def icon_compass(c, x, y, a):
    c.new_path(); c.arc(x, y, 34, 0, 2 * math.pi); c.set_line_width(6); c.set_source_rgba(*NAVY, a); c.stroke()
    c.new_path(); c.move_to(x, y - 30); c.line_to(x + 10, y); c.line_to(x, y + 30); c.line_to(x - 10, y); c.close_path(); fill(c, TERRA, a)

def sc_pillars(c, t, d):
    """Creencia y método de los Compañeros."""
    T = t + 14.5
    sky(c, hx("CFE3E0"), hx("EAF3EE")); ground(c, SAND)
    base = GROUND + 10
    pillar(c, CX - 220, base, 520, 150, TEAL, "Creencia", icon_heart, (T - 14.7) / 1.2)
    pillar(c, CX + 220, base, 520, 150, TEAL, "Método", icon_compass, (T - 17.6) / 1.2)
    if T > 18.8:
        k = ease((T - 18.8) / 0.6)
        top = base - 520 - 24
        c.new_path(); c.move_to(CX - 320, top); c.line_to(CX - 320, top - 40 * k); c.curve_to(CX - 300, top - 260 * k, CX + 300, top - 260 * k, CX + 320, top - 40 * k); c.line_to(CX + 320, top); c.close_path(); fill(c, GOLD_, k)
        text_c(c, "Los Compañeros", CX, top - 80 * k, 38, CREAM, k)

def sc_clarity(c, t, d):
    """Cuando las cosas se confunden, decirlo es necesario."""
    T = t + 21.5
    sky(c, hx("F3E6D2"), hx("FBF6EE"))
    u = ease_io(clamp((T - 23.0) / 2.5))
    cols = [TERRA, NAVY, OLIVE, TEAL, SAND, BROWN]
    for j, col in enumerate(cols):
        c.new_path()
        for i in range(60):
            s = i / 59
            x = PX + 80 + s * (PW - 160)
            ny = CY + math.sin(s * 9 + j * 1.3 + T * 2) * 220 * (1 - s * 0.2) + math.cos(s * 17 + j) * 120
            y = lerp(ny, CY + (j - 2.5) * 6, u)
            (c.move_to if i == 0 else c.line_to)(x, y)
        c.set_line_width(12); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_source_rgba(*(GOLD_ if u > 0.9 else col), 0.85); c.stroke()
    tag(c, CX, PY + 120, "Confusión" if T < 25 else "Claridad", TERRA if T < 25 else DKGREEN, CREAM, 44, 1)
    if T > 25.3: check(c, CX, CY + 220, 54, (T - 25.3) / 0.4)

BOOKS = [(27.0, "Imames del Islam", NAVY), (28.5, "Ibn Taymiyyah", TERRA), (35.0, "Ibn Baz", TEAL), (39.0, "Ibn Uzaimín", OLIVE), (40.8, "Al-Fawzán", BROWN)]

def sc_scholars(c, t, d):
    """Los imames y sabios: atribuirse a los Salaf es bueno y loable."""
    T = t + 27.0
    sky(c, hx("F6E2C4"), hx("FBF1E0"))
    # estantería
    shelf_y = GROUND - 40
    rrect(c, PX + 60, shelf_y, PW - 120, 30, 8); fill(c, BROWN)
    rrect(c, PX + 60, shelf_y - 470, PW - 120, 30, 8); fill(c, BROWN)
    for i, (st, name, col) in enumerate(BOOKS):
        k = (T - st) / 0.5
        if k <= 0: continue
        x = PX + 150 + i * 170
        hh = 400 - (i % 2) * 40
        with pop(c, x + 60, shelf_y, k):
            rrect(c, x, shelf_y - hh, 120, hh, 10); fill(c, col)
            rrect(c, x + 10, shelf_y - hh + 30, 100, 10, 5); fill(c, GOLD_)
            rrect(c, x + 10, shelf_y - 50, 100, 10, 5); fill(c, GOLD_)
            c.save(); c.translate(x + 74, shelf_y - 80); c.rotate(-math.pi / 2)
            font(c, 30 if len(name) < 14 else 26, True); c.move_to(0, 0); c.set_source_rgb(*CREAM); c.show_text(name); c.restore()
    if T < 28.5: tag(c, CX, PY + 110, "Los imames del Islam", NAVY, CREAM, 40, ease((T - 27.0) / 0.4))
    elif T < 35.0: tag(c, CX, PY + 110, "No hay reproche", DKGREEN, CREAM, 40, ease((T - 29.5) / 0.4))
    elif T < 43.0: tag(c, CX, PY + 110, "Nuestros imames y sabios", NAVY, CREAM, 40, 1)
    if T > 43.0:
        k = (T - 43.0) / 0.6
        with pop(c, CX, PY + 220, k):
            for i in range(12):
                a = i * math.pi / 6 + T * 0.4
                line(c, CX, PY + 220, CX + math.cos(a) * 150, PY + 220 + math.sin(a) * 150, 12, GLOW, 0.6)
            circle(c, CX, PY + 220, 110, GOLD_)
            star(c, CX, PY + 220, 60, CREAM)
        tag(c, CX, PY + 400, "Bueno y loable", GOLD_, CREAM, 42, ease(k))

def lamp(c, x, base, h, on):
    line(c, x, base, x, base - h, 10, NAVY)
    rrect(c, x - 26, base - h - 50, 52, 60, 10); fill(c, NAVY)
    circle(c, x, base - h - 20, 18, GLOW if on else GREY)
    if on:
        for i in range(3): circle(c, x, base - h - 20, 30 + i * 18, GLOW, 0.12)

def sc_obligatory(c, t, d):
    """Ibn Uzaimín: es obligatorio en cuanto a seguirlos."""
    T = t + 49.0
    sky(c, hx("CFE3E0"), hx("F3E6D2")); ground(c, OLIVE)
    c.new_path(); c.move_to(CX - 60, GROUND - 120); c.line_to(CX + 60, GROUND - 120); c.line_to(CX + 380, PY + PH); c.line_to(CX - 380, PY + PH); c.close_path(); fill(c, hx("E9D3A8"))
    for i in range(4):
        u = i / 4
        y = lerp(PY + PH - 20, GROUND - 110, u); s = lerp(1.0, 0.45, u)
        on = T > 50.5 + i * 0.7
        lamp(c, CX - lerp(380, 70, u) - 30, y, 260 * s, on)
        lamp(c, CX + lerp(380, 70, u) + 30, y, 260 * s, on)
    # libro de Ibn Uzaimín
    with pop(c, CX, PY + 260, (T - 49.2) / 0.5):
        rrect(c, CX - 150, PY + 140, 300, 220, 16); fill(c, OLIVE)
        rrect(c, CX - 130, PY + 160, 260, 180, 10); fill(c, CREAM)
        text_c(c, "Ibn Uzaimín", CX, PY + 262, 34, NAVY)
    if T > 52.5:
        k = (T - 52.5) / 0.4
        with pop(c, CX + 260, PY + 380, k):
            c.save(); c.translate(CX + 260, PY + 380); c.rotate(-0.15)
            rrect(c, -200, -50, 400, 100, 16); c.set_line_width(10); c.set_source_rgb(*RED); c.stroke()
            text_c(c, "OBLIGATORIO", 0, 18, 50, RED); c.restore()
    if T > 54.5:
        u = ease((T - 54.5) / 4.0)
        bob = abs(math.sin(T * 7)) * 8
        person(c, CX, lerp(GROUND + 150, GROUND - 30, u) - bob, lerp(360, 230, u), TEAL, cap=CREAM)
        tag(c, CX, PY + PH - 60, "Seguir a los Salaf", DKGREEN, CREAM, 36, ease((T - 54.7) / 0.4))

SCENES = [
    (0.0, 7.5, sc_muslim, PANEL), (7.5, 14.5, sc_path, PANEL), (14.5, 21.5, sc_pillars, PANEL),
    (21.5, 27.0, sc_clarity, PANEL), (27.0, 49.0, sc_scholars, PANEL), (49.0, SPEECH_END, sc_obligatory, PANEL),
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
