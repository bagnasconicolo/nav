"""Annotated sheets (A3 landscape, 300 dpi): the exploded view with numbered balloons and a parts
legend, and the two electronics modules with text callouts.

The anchors come from the model itself: scene_v14.py with ANNOT=<file>.json (and NORENDER=1) writes,
for the same camera as the render, where every part lands in the image.

    python tavola_annotata.py <renders_dir> <annot_dir> <out_dir>
      renders_dir: exploded.png, acq_open.png, compute_open.png (transparent background)
      annot_dir:   exploded.json, acq_open.json, compute_open.json
"""
import json
import os
import sys
from datetime import date

from PIL import Image, ImageDraw, ImageFont

DPI = 300
PX = DPI / 25.4
A3 = (round(420 * PX), round(297 * PX))
FD = '/usr/share/fonts/opentype/inter/'
INK = (28, 28, 32)
ACCENT = (200, 85, 20)
GREY = (118, 118, 124)
LINE = (60, 60, 66)


def font(size_mm, w='Regular'):
    return ImageFont.truetype(FD + f'Inter-{w}.otf', round(size_mm * PX))


def mm(v):
    return round(v * PX)


def header(im, title, sub):
    d = ImageDraw.Draw(im)
    d.text((mm(14), mm(10)), title, font=font(8, 'Bold'), fill=INK)
    d.text((mm(14), mm(21)), sub, font=font(4), fill=GREY)
    d.line((mm(14), mm(28), A3[0] - mm(14), mm(28)), fill=ACCENT, width=mm(0.7))
    d.text((mm(14), A3[1] - mm(10)), f'MuLab · rivelatore di muoni a tre barre   ·   modello v14   ·   {date.today().strftime("%d/%m/%Y")}',
           font=font(3), fill=GREY)


def place(im, src, pts, box, crop=None):
    """Paste the render (cropped to its content or to `crop`) on white inside box=(x0,y0,x1,y1);
    return the anchor points mapped to page pixels."""
    if src.mode == 'RGBA':
        import numpy as np
        a = np.array(src).astype(float)
        dark = a[:, :, :3].max(2) < 40                      # shadow-catcher pixels are black with partial alpha
        al = a[:, :, 3]
        al[dark] = np.clip((al[dark] - 70.0) * 1.6, 0, 255)
        a[:, :, 3] = al
        src = Image.fromarray(a.astype('uint8'), 'RGBA')
    if crop is None:
        bb = src.getchannel('A').point(lambda v: 255 if v > 40 else 0).getbbox()
        e = 90
        crop = (max(0, bb[0] - e), max(0, bb[1] - e), min(src.width, bb[2] + e), min(src.height, bb[3] + e))
    c = src.crop(crop)
    s = min((box[2] - box[0]) / c.width, (box[3] - box[1]) / c.height)
    c = c.resize((round(c.width * s), round(c.height * s)), Image.LANCZOS)
    ox = box[0] + (box[2] - box[0] - c.width) // 2
    oy = box[1] + (box[3] - box[1] - c.height) // 2
    im.paste(c, (ox, oy), c)
    return {k: (ox + (x - crop[0]) * s, oy + (y - crop[1]) * s) for k, (x, y) in pts.items()}, (ox, oy, ox + c.width, oy + c.height), c


def spread(ys, lo, hi, gap):
    """Keep the order, push apart to at least `gap`, stay inside [lo, hi]."""
    ys = [min(max(y, lo), hi) for y in ys]
    for _ in range(50):
        for i in range(1, len(ys)):
            ys[i] = max(ys[i], ys[i - 1] + gap)
        if ys and ys[-1] > hi:
            ys[-1] = hi
            for i in range(len(ys) - 2, -1, -1):
                ys[i] = min(ys[i], ys[i + 1] - gap)
    return ys


def leader(d, p0, p1):
    d.line((p0, p1), fill='white', width=mm(0.75))
    d.line((p0, p1), fill=LINE, width=mm(0.25))
    r = mm(0.9)
    d.ellipse((p1[0] - r, p1[1] - r, p1[0] + r, p1[1] + r), fill=ACCENT, outline='white', width=mm(0.25))


def balloon(d, c, n, r):
    d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill='white', outline=ACCENT, width=mm(0.5))
    d.text(c, str(n), font=font(4.2, 'SemiBold'), fill=INK, anchor='mm')


# ---------------------------------------------------------------- sheet 1: exploded + legend
LEGEND = [
    ('Telaio', [
        ('piede', 'Piede', '2 · PETG antracite, inserti M4 per il modulo scheda'),
        ('montante', 'Montante Bosch 20 × 20, 250 mm', '2 · alluminio, estremità maschiate M5'),
        ('traversa', 'Traversa Bosch 20 × 20, 300 mm', '1 · nella sua cava posteriore corrono i cavi'),
        ('tappo', 'Tappo del montante', '2 · vite M5 svasata, blocca la colonna'),
        ('vite_piede', 'Vite M5 × 16 ISO 4762', '2 · dal basso, piede → montante'),
        ('vite_m5', 'Vite M5 × 8 ISO 7380', '2 · piede → traversa'),
        ('dado_t', 'Dado a T M5', '2 · nella cava inferiore della traversa'),
        ('gommino', 'Gommino adesivo Ø 12 mm', '12 · sotto piedi, culle e ponte'),
    ]),
    ('Rivelatore', [
        ('barra', 'Barra di scintillatore 300 × 45 × 5 mm', '3 · rivestita, a tenuta di luce'),
        ('aggancio', 'Aggancio della barra', '6 · PETG arancio, numerati 1–3'),
        ('distanziale', 'Distanziali 24 / 50 / 44 mm', '8 · fissano la quota delle barre'),
        ('circuito_barra', 'Circuito della barra (SiPM)', '3 · connettore Molex KK 254'),
        ('copertura', 'Copertura del circuito', '3 · lascia libero il connettore'),
    ]),
    ('Modulo scheda', [
        ('scheda3ch', 'Scheda di lettura a 3 canali', '1 · 103 × 224 mm, USB-C, uscite LEMO'),
        ('culla', 'Culla laterale', '2 · distanziali M3 in ottone'),
        ('ponte', 'Ponte centrale', '1 · sostiene il centro della scheda'),
        ('pomello_m4', 'Pomello M4', '4 · si svitano e il modulo si stacca'),
    ]),
    ('Moduli elettronici', [
        ('scatola_acq', 'Scatola di acquisizione', '1 · Pico 2, GPS, 5 LEMO; montante destro'),
        ('coperchio_acq', 'Coperchio della scatola di acquisizione', '1 · 4 viti M3, feritoie sopra il Pico'),
        ('scatola_calc', 'Modulo di calcolo', '1 · Raspberry Pi Zero 2 W con ventola; montante sinistro'),
        ('meteo', 'Modulo meteo su supporto', '1 · SHT45 + LPS22HH, cavo Qwiic'),
    ]),
]


def sheet_exploded(rdir, adir):
    im = Image.new('RGB', A3, 'white')
    header(im, 'Esploso annotato', 'Tutti i pezzi del rivelatore MuLab. Numeri = voci della legenda, quantità per un rivelatore.')
    src = Image.open(os.path.join(rdir, 'exploded.png')).convert('RGBA')
    pts = json.load(open(os.path.join(adir, 'exploded.json')))['pts']
    box = (mm(46), mm(34), mm(268), mm(282))
    P, ib, cimg = place(im, src, pts, box)
    d = ImageDraw.Draw(im)
    num = {}
    k = 1
    for _, items in LEGEND:
        for key, *_ in items:
            num[key] = k
            k += 1
    # balloons: for every anchor, the nearest free spot outside the parts, in the outward direction
    r = mm(4.0)
    import math
    from PIL import ImageFilter
    q = 4                                                    # work on a 1/4 grid
    mask = Image.new('L', A3, 0)
    mask.paste(cimg.getchannel('A'), (ib[0], ib[1]))
    mask = mask.resize((A3[0] // q, A3[1] // q)).point(lambda v: 255 if v > 60 else 0)
    mask = mask.filter(ImageFilter.MaxFilter(9))
    M = mask.load()
    cx, cy = (ib[0] + ib[2]) / 2, (ib[1] + ib[3]) / 2
    placed, segs = [], []

    def free(x, y):
        if not (mm(18) < x < mm(290) and mm(36) < y < mm(284)):
            return False
        for a_ in range(0, 360, 30):
            px, py = x + (r + mm(1)) * math.cos(math.radians(a_)), y + (r + mm(1)) * math.sin(math.radians(a_))
            if M[int(px / q), int(py / q)]:
                return False
        return all(math.hypot(x - u, y - v) > 2 * r + mm(2.5) for u, v in placed)

    def cross(p, q_, a, b):
        def o(u, v, w):
            return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
        return o(p, q_, a) * o(p, q_, b) < 0 and o(a, b, p) * o(a, b, q_) < 0

    order = sorted(num, key=lambda k: -math.hypot(P[k][0] - cx, P[k][1] - cy))
    for k in order:
        ax, ay = P[k]
        out = math.atan2(ay - cy, ax - cx)
        best = None
        for da in range(-90, 91, 10):
            ang = out + math.radians(da)
            for dist in range(mm(10), mm(140), mm(2)):
                x, y = ax + dist * math.cos(ang), ay + dist * math.sin(ang)
                if free(x, y):
                    ncross = sum(cross((ax, ay), (x, y), s0, s1) for s0, s1 in segs)
                    cost = dist + abs(da) * mm(0.25) + ncross * mm(60)
                    if best is None or cost < best[0]:
                        best = (cost, x, y)
                    break
        _, x, y = best
        placed.append((x, y))
        segs.append(((ax, ay), (x, y)))
        d_ = math.hypot(ax - x, ay - y)
        leader(d, (x + (ax - x) * r / d_, y + (ay - y) * r / d_), (ax, ay))
        balloon(d, (x, y), num[k], r)
    # legend
    x0, y = mm(302), mm(38)
    for grp, items in LEGEND:
        d.text((x0, y), grp.upper(), font=font(3.4, 'Bold'), fill=ACCENT)
        y += mm(6.5)
        for key, name, det in items:
            balloon(d, (x0 + mm(3.6), y + mm(3.1)), num[key], mm(3.4))
            d.text((x0 + mm(10), y), name, font=font(3.5, 'SemiBold'), fill=INK)
            d.text((x0 + mm(10), y + mm(4.6)), det, font=font(2.9), fill=GREY)
            y += mm(10.4)
        y += mm(3.0)
    d.line((mm(296), mm(36), mm(296), mm(282)), fill=(220, 220, 224), width=mm(0.3))
    return im


# ---------------------------------------------------------------- sheet 2: the electronics modules
ACQ = {
    'pico': ('Raspberry Pi Pico 2 su zoccolo', 'conta gli impulsi e ne marca il tempo'),
    'hub': ('Hub I²C TCA9548A', '8 porte: 2 KK verso i rivelatori, 6 Qwiic'),
    'porte_i2c': ('Porte I²C e Qwiic', 'dalla feritoia sul retro della scatola'),
    'lemo_in': ('Ingressi LEMO 1, 2, 3, AND', 'dalle uscite della scheda a 3 canali'),
    'lemo_pps': ('Uscita PPS (LEMO)', '1 impulso al secondo, per l\'oscilloscopio'),
    'gps': ('GPS u-blox NEO-M9N', 'ora UTC esatta e PPS'),
    'dupont': ('Cavetti del GPS', '5V · 3V3 · GND · TX · RX · PPS'),
    'sma': ('Antenna GPS (SMA)', 'cavo 3–5 m verso la finestra'),
    'usb_pico': ('USB del Pico', 'dati e alimentazione dallo Zero 2 W'),
    'coperchio_acq': ('Coperchio', '4 viti M3 in inserti, feritoie sopra il Pico'),
    'pomello_m5': ('Pomello M5', 'dado a T nella cava del montante destro'),
}
CALC = {
    'zero': ('Raspberry Pi Zero 2 W', 'archivio, sensori, dashboard Wi-Fi'),
    'gpio': ('Connettore GPIO 2 × 20', 'raggiungibile dalla finestra del coperchio'),
    'microsd': ('Scheda microSD', 'i dati delle misure'),
    'porte_usb': ('Porte USB, sul retro', 'PWR (alimentatore 5 V) e dati (al Pico)'),
    'ventola': ('Ventola 30 mm', 'sotto la griglia del coperchio'),
    'coperchio_calc': ('Coperchio con finestra GPIO', '3 viti M3 svasate'),
    'pomello_calc': ('Pomello M5', 'dado a T nella cava del montante sinistro'),
    'meteo_scheda': ('Modulo meteo SHT45 + LPS22HH', 'temperatura, umidità, pressione (Qwiic)'),
    'supporto_meteo': ('Supporto con tettoia', 'sotto lo Zero, lontano dal suo calore'),
}


def callouts(d, P, labels, side, xcol, lo, hi):
    keys = sorted(labels, key=lambda k: P[k][1])
    ys = spread([P[k][1] for k in keys], lo, hi, mm(13.5))
    for k, y in zip(keys, ys):
        name, det = labels[k]
        if side < 0:
            d.text((xcol, y - mm(1.2)), name, font=font(3.5, 'SemiBold'), fill=INK, anchor='rs')
            d.text((xcol, y + mm(1.0)), det, font=font(2.9), fill=GREY, anchor='rt')
            p0, p1 = (xcol + mm(2), y), (xcol + mm(8), y)
        else:
            d.text((xcol, y - mm(1.2)), name, font=font(3.5, 'SemiBold'), fill=INK, anchor='ls')
            d.text((xcol, y + mm(1.0)), det, font=font(2.9), fill=GREY, anchor='lt')
            p0, p1 = (xcol - mm(2), y), (xcol - mm(8), y)
        d.line((p0, p1), fill=LINE, width=mm(0.25))
        leader(d, p1, P[k])


def rounded(im, rad):
    m_ = Image.new('L', im.size, 0)
    ImageDraw.Draw(m_).rounded_rectangle((0, 0, im.width - 1, im.height - 1), rad, fill=255)
    return m_


def sheet_modules(rdir, adir):
    im = Image.new('RGB', A3, 'white')
    header(im, 'Moduli elettronici', 'A destra del telaio la scatola di acquisizione, a sinistra il modulo di calcolo con il modulo meteo. Coperchi aperti.')
    d = ImageDraw.Draw(im)
    panels = [('acq_open', ACQ, 'Scatola di acquisizione · montante destro', -1, (mm(78), mm(46)), (560, 140, 1540, 1500)),
              ('compute_open', CALC, 'Modulo di calcolo e modulo meteo · montante sinistro', 1, (mm(213), mm(46)), (620, 330, 1360, 1400))]
    for name, labels, title, side, (x0, y0), crop in panels:
        src = Image.open(os.path.join(rdir, name + '_c.png')).convert('RGB')
        pts = json.load(open(os.path.join(adir, name + '.json')))['pts']
        c = src.crop(crop)
        s_ = min(mm(129) / c.width, mm(222) / c.height)
        c = c.resize((round(c.width * s_), round(c.height * s_)), Image.LANCZOS)
        y0 = mm(50)
        im.paste(c, (x0, y0), rounded(c, mm(4)))
        P = {k: (x0 + (pts[k][0] - crop[0]) * s_, y0 + (pts[k][1] - crop[1]) * s_) for k in labels}
        d.text((x0 + c.width // 2, y0 - mm(4)), title, font=font(4, 'Bold'), fill=ACCENT, anchor='ms')
        xcol = x0 - mm(10) if side < 0 else x0 + c.width + mm(10)
        callouts(d, P, labels, side, xcol, y0 + mm(6), y0 + c.height - mm(6))
    return im


if __name__ == '__main__':
    rdir, adir, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    a = sheet_exploded(rdir, adir)
    b = sheet_modules(rdir, adir)
    a.save(os.path.join(out, 'esploso_annotato_1.png'))
    b.save(os.path.join(out, 'esploso_annotato_2.png'))
    a.save(os.path.join(out, 'MuLab_esploso_annotato.pdf'), save_all=True, append_images=[b], resolution=DPI)
    print('ok')
