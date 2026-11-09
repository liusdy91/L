"""Animación flat vector «Du'a: te encomiendo mi asunto» (1080x1920), subtítulos en español y marca de agua «Casa Antigua».

Uso: python3 animacion_flat.py <video_o_audio_original> <salida.mp4> [segundo_preview]
"""
import math, subprocess, sys
import cairo

SRC = sys.argv[1]
OUT = sys.argv[2]
PREVIEW = float(sys.argv[3]) if len(sys.argv) > 3 else None
W, H, FPS = 1080, 1920, 30
SPEECH_END = 16.2
END_CARD = 4.0
TOTAL = SPEECH_END + END_CARD

def hx(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) / 255 for i in (0, 2, 4))

BG = hx("F4EBDD"); PANEL = hx("FBF6EE"); NAVY = hx("1F3A4D"); TEAL = hx("2A7F7A")
TERRA = hx("C8603C"); SAND = hx("E3B964"); OLIVE = hx("7E8B4F"); CREAM = hx("FFFDF8")
SKY = hx("CFE3E0"); RED = hx("D2453A"); BROWN = hx("8A5A3B"); GREY = hx("B9B2A6")
SKIN = hx("D9A47E")

SUBS = [
(0.8,4.0,"Oh Allah, Tú conoces mi *situación*"),
(4.0,7.0,"y sabes lo que *mejora* mi situación."),
(7.0,10.0,"Oh Allah, Tú sabes *quién* me ha hecho *daño*"),
(10.0,13.9,"y sabes lo que me *sana* y *aleja* mi daño."),
(13.9,SPEECH_END,"Oh Allah, a Ti te *encomiendo* mi asunto."),
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

SPEAKER = "Du'a · Súplica"

import io
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

GOLD_ = hx("C9A060"); NIGHT = hx("1E2F4A"); NIGHT2 = hx("2B4466"); GLOW = hx("FFE7A8")
DUA = [
    (0.0, 4.0, "اللَّهُمَّ إِنَّكَ تَعْلَمُ بِحَالِي"),
    (4.0, 7.0, "وَتَعْلَمُ مَا يُصْلِحُ حَالِي"),
    (7.0, 10.0, "اللَّهُمَّ إِنَّكَ تَعْلَمُ مَنْ ضَرَّنِي"),
    (10.0, 13.9, "وَتَعْلَمُ مَا يُصْلِحُ وَيُذْهِبُ ضُرِّي"),
    (13.9, SPEECH_END, "اللَّهُمَّ إِنِّي أَكِلُ إِلَيْكَ أَمْرِي"),
]
DUA_S = [arabic_surface(x[2], 70, CREAM) for x in DUA]

def star(c, x, y, r, col, a=1.0):
    if r <= 0: return
    c.new_path()
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.42
        ang = -math.pi / 2 + i * math.pi / 5
        (c.move_to if i == 0 else c.line_to)(x + math.cos(ang) * rr, y + math.sin(ang) * rr)
    c.close_path(); fill(c, col, a)

def night_sky(c, t, top=NIGHT, bottom=NIGHT2):
    g = cairo.LinearGradient(0, PY, 0, PY + PH)
    g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(1, *bottom)
    c.rectangle(PX, PY, PW, PH); c.set_source(g); c.fill()
    for i in range(26):
        k = (t * 0.35 + i * 0.37) % 1
        star(c, PX + 30 + (i * 137) % (PW - 60), PY + 40 + (i * 71) % 520, 9 * (0.35 + 0.65 * math.sin(k * math.pi)), CREAM, 0.85)

def crescent(c, x, y, r, col=SAND):
    c.new_path(); c.arc(x, y, r, 0, 2 * math.pi); c.arc_negative(x + r * 0.42, y - r * 0.25, r * 0.86, 2 * math.pi, 0)
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); fill(c, col); c.set_fill_rule(cairo.FILL_RULE_WINDING)

def dua_text(c, i, t):
    s, e, _ = DUA[i]
    k = ease(t / 0.6)
    surf = DUA_S[i]; sc = min(1.0, 820 / surf.get_width())
    rrect(c, CX - 440, PY + 60, 880, 150, 40); fill(c, (0, 0, 0), 0.22 * k)
    blit(c, surf, CX, PY + 135 + (1 - k) * 20, k, sc)

def mat(c, x, base, w):
    rrect(c, x - w / 2, base - 26, w, 34, 10); fill(c, hx("8E3B2E"))
    rrect(c, x - w / 2 + 14, base - 20, w - 28, 22, 6); fill(c, TERRA)
    for i in range(5):
        rrect(c, x - w / 2 + 30 + i * (w - 60) / 5, base - 14, (w - 60) / 5 - 14, 10, 4); fill(c, GOLD_, 0.8)

def praying(c, x, base, s, t, lift=1.0, col=TEAL):
    """Persona sin rostro, de rodillas sobre la alfombra, con ambas palmas alzadas en súplica."""
    c.save(); c.translate(x, base); c.scale(s, s)
    rrect(c, -150, -60, 300, 60, 30); fill(c, NAVY)                        # rodillas
    c.new_path(); c.move_to(-120, -30); c.curve_to(-125, -220, -80, -300, 0, -300)
    c.curve_to(80, -300, 125, -220, 120, -30); c.close_path(); fill(c, col)  # torso
    br = math.sin(t * 2.2) * 4
    up = 40 * lift
    for sx in (-1, 1):
        sh = (sx * 78, -250); el = (sx * 118, -140); hd = (sx * 70, -190 - up + br)
        c.new_path(); c.set_line_width(34); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.move_to(*sh); c.line_to(*el); c.line_to(hd[0], hd[1] + 30); c.set_source_rgb(*hx("236B67") if col == TEAL else col); c.stroke()
        c.new_path(); c.save(); c.translate(hd[0], hd[1]); c.rotate(sx * 0.35); c.scale(0.62, 1.15); c.arc(0, 0, 30, 0, 2 * math.pi); c.restore(); fill(c, SKIN)
    circle(c, 0, -360, 62, SKIN)                                             # cabeza
    c.new_path(); c.arc(0, -372, 64, math.pi, 2 * math.pi); fill(c, CREAM)   # gorro
    c.restore()

def light_beam(c, x, top, base, w, a):
    g = cairo.LinearGradient(0, top, 0, base)
    g.add_color_stop_rgba(0, *GLOW, 0.75 * a); g.add_color_stop_rgba(1, *GLOW, 0.05 * a)
    c.new_path(); c.move_to(x - w * 0.25, top); c.line_to(x + w * 0.25, top); c.line_to(x + w / 2, base); c.line_to(x - w / 2, base); c.close_path()
    c.set_source(g); c.fill()

def ground_night(c):
    c.new_path(); c.move_to(PX, GROUND - 30); c.curve_to(PX + 300, GROUND - 80, PX + 650, GROUND - 10, PX + PW, GROUND - 60)
    c.line_to(PX + PW, PY + PH); c.line_to(PX, PY + PH); c.close_path(); fill(c, hx("16243A"))

def mosque_sil(c, x, base, s, col):
    c.new_path(); c.arc(x, base - 120 * s, 80 * s, math.pi, 2 * math.pi); fill(c, col)
    rrect(c, x - 120 * s, base - 120 * s, 240 * s, 120 * s, 0); fill(c, col)
    for sx in (-1, 1):
        rrect(c, x + sx * 160 * s - 16 * s, base - 280 * s, 32 * s, 280 * s, 0); fill(c, col)
        c.new_path(); c.move_to(x + sx * 160 * s - 22 * s, base - 280 * s); c.line_to(x + sx * 160 * s + 22 * s, base - 280 * s); c.line_to(x + sx * 160 * s, base - 330 * s); c.close_path(); fill(c, col)

# --- escenas
def sc_know(c, t, d):
    night_sky(c, t)
    crescent(c, PX + PW - 180, PY + 330, 70)
    mosque_sil(c, PX + 230, GROUND - 40, 1.0, hx("223553"))
    ground_night(c)
    light_beam(c, CX, PY + 220, GROUND + 20, 420, ease(t / 1.5))
    mat(c, CX, GROUND + 40, 420)
    praying(c, CX + 10, GROUND + 14, 1.0, t, ease(t / 0.8))
    dua_text(c, 0, t)

def plant(c, x, base, g, wilt):
    line(c, x, base, x + 40 * wilt, base - 240 * g, 14, OLIVE)
    for i in range(3):
        yy = base - 80 - i * 60
        if base - yy > 240 * g: break
        s = 1 if i % 2 else -1
        c.save(); c.translate(x + 40 * wilt * (base - yy) / 240, yy); c.rotate(s * (0.5 + wilt * 0.9)); c.scale(g, g)
        c.new_path(); c.move_to(0, 0); c.curve_to(s * 30, -40, s * 90, -30, s * 110, 0); c.curve_to(s * 80, 25, s * 30, 25, 0, 0); fill(c, TEAL)
        c.restore()
    if g > 0.9 and wilt < 0.2:
        k = ease((g - 0.9) / 0.1)
        for i in range(5):
            circle(c, x + math.cos(i * 1.26) * 34, base - 250 + math.sin(i * 1.26) * 34, 22 * k, SAND)
        circle(c, x, base - 250, 20 * k, TERRA)

def sc_fix(c, t, d):
    night_sky(c, t, hx("23385A"), hx("3A5B7E"))
    crescent(c, PX + PW - 180, PY + 330, 70)
    ground_night(c)
    # gotas de luz que caen sobre la planta marchita, que revive
    for i in range(12):
        k = (t * 0.8 + i / 12) % 1
        circle(c, CX - 160 + (i * 53) % 320, PY + 260 + k * 520, 7, GLOW, (1 - k) * ease(t / 0.6))
    revive = ease((t - 0.6) / 2.0)
    rrect(c, CX - 70, GROUND - 40, 140, 100, 14); fill(c, TERRA)
    plant(c, CX, GROUND - 40, 0.75 + 0.25 * revive, 1 - revive)
    dua_text(c, 1, t)

def cloud(c, x, y, s, col, a=1.0):
    for dx, dy, r in ((-80, 10, 60), (-20, -30, 80), (60, 0, 65), (110, 20, 45), (-130, 25, 40)):
        circle(c, x + dx * s, y + dy * s, r * s, col, a)
    rrect(c, x - 160 * s, y + 10 * s, 300 * s, 60 * s, 30 * s); fill(c, col, a)

def bolt(c, x, y, s, a):
    c.new_path(); c.move_to(x, y); c.line_to(x - 40 * s, y + 110 * s); c.line_to(x - 5 * s, y + 105 * s)
    c.line_to(x - 30 * s, y + 220 * s); c.line_to(x + 45 * s, y + 80 * s); c.line_to(x + 8 * s, y + 85 * s); c.line_to(x + 30 * s, y); c.close_path(); fill(c, SAND, a)

def sc_harm(c, t, d):
    flash = max(0, math.sin(t * 4.0)) ** 12
    night_sky(c, t, hx("1B2436"), hx("2C3446"))
    c.rectangle(PX, PY, PW, PH); c.set_source_rgba(*CREAM, 0.15 * flash); c.fill()
    ground_night(c)
    for i in range(30):
        k = (t * 1.6 + i / 30) % 1
        line(c, PX + (i * 89) % PW, PY + 330 + k * 600, PX + (i * 89) % PW - 12, PY + 360 + k * 600, 4, SKY, 0.5)
    cloud(c, CX - 160, PY + 330 + math.sin(t) * 6, 1.3, hx("4A5568"))
    cloud(c, CX + 200, PY + 380 + math.sin(t + 1) * 6, 1.0, hx("5A6578"))
    bolt(c, CX + 160, PY + 420, 1.1, flash)
    mat(c, CX - 40, GROUND + 40, 420)
    praying(c, CX - 30, GROUND + 14, 1.0, t, 1.0, col=hx("3A7F7A"))
    # escudo de luz alrededor de quien suplica
    c.new_path(); c.arc(CX - 30, GROUND - 160, 280, math.pi, 2 * math.pi); c.set_line_width(10); c.set_source_rgba(*GLOW, 0.35 + 0.15 * math.sin(t * 3)); c.stroke()
    dua_text(c, 2, t)

def sc_relief(c, t, d):
    k = ease(t / 2.0)
    top = tuple(lerp(a, b, k) for a, b in zip(hx("2C3446"), hx("F4C98A")))
    bot = tuple(lerp(a, b, k) for a, b in zip(hx("3A4458"), hx("FBE6C2")))
    night_sky(c, t * (1 - k), top, bot)
    # sol que sale
    sy = GROUND - 40 - 360 * k
    for i in range(14):
        a = i * math.pi / 7 + t * 0.2
        line(c, CX + math.cos(a) * 170, sy + math.sin(a) * 170, CX + math.cos(a) * (230 + 30 * k), sy + math.sin(a) * (230 + 30 * k), 18, SAND, k)
    circle(c, CX, sy, 140, SAND); circle(c, CX, sy, 100, hx("EFC977"))
    # arcoíris
    if t > 1.6:
        r = ease((t - 1.6) / 1.4)
        for j, col in enumerate((TERRA, SAND, OLIVE, TEAL)):
            c.new_path(); c.set_line_width(26); c.arc(CX, GROUND + 60, 520 - j * 28, math.pi, math.pi + math.pi * r)
            c.set_source_rgba(*col, 0.85); c.stroke()
    # las nubes se van
    cloud(c, CX - 160 - 600 * k, PY + 330, 1.3, hx("4A5568"), 1 - k)
    cloud(c, CX + 200 + 600 * k, PY + 380, 1.0, hx("5A6578"), 1 - k)
    c.new_path(); c.move_to(PX, GROUND - 30); c.curve_to(PX + 300, GROUND - 80, PX + 650, GROUND - 10, PX + PW, GROUND - 60)
    c.line_to(PX + PW, PY + PH); c.line_to(PX, PY + PH); c.close_path(); fill(c, tuple(lerp(a, b, k) for a, b in zip(hx("16243A"), OLIVE)))
    mat(c, CX - 40, GROUND + 40, 420)
    praying(c, CX - 30, GROUND + 14, 1.0, t, 1.0)
    dua_text(c, 3, t)

def sc_trust(c, t, d):
    night_sky(c, t, hx("1E2F4A"), hx("35557A"))
    crescent(c, CX, PY + 330, 80)
    ground_night(c)
    a = ease(t / 0.8)
    light_beam(c, CX, PY + 250, GROUND + 20, 560, a)
    mat(c, CX, GROUND + 40, 420)
    praying(c, CX + 10, GROUND + 14, 1.0, t, 1.0)
    # partículas de luz que suben
    for i in range(16):
        k = (t * 0.5 + i / 16) % 1
        circle(c, CX - 200 + (i * 29) % 400, GROUND - 100 - k * 560, 6 + 4 * math.sin(i), GLOW, (1 - k) * a)
    dua_text(c, 4, t)

SCENES = [
    (0.0, 4.0, sc_know, NIGHT), (4.0, 7.0, sc_fix, NIGHT), (7.0, 10.0, sc_harm, NIGHT),
    (10.0, 13.9, sc_relief, NIGHT), (13.9, SPEECH_END, sc_trust, NIGHT),
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
