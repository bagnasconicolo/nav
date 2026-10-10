"""Assemble the MuLab PDF: overview renders, one page per printed part, and a technical sheet
(three orthographic views in first-angle projection + overall dimensions + axonometric render)
for every part, at true scale on A4 landscape (print at 100%).

    python make_pdf.py <renders_dir> <parts_dir> <views_dir> <out.pdf>
"""
import json
import os
import sys
from datetime import date

from PIL import Image, ImageDraw, ImageFont

DPI = 300
PX = DPI / 25.4                       # px per mm on paper
A4 = (round(297 * PX), round(210 * PX))
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
INK = (25, 25, 28)
ACCENT = (200, 85, 20)
GREY = (120, 120, 125)


def f(size_mm, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, round(size_mm * PX))


def mm(v):
    return round(v * PX)


PARTS = [  # file stem, display name, quantity, notes
    ('piede', 'Piede', '2', 'Stesso pezzo a destra e a sinistra (ruotato di 180°). 4 inserti M4 sul fianco interno.'),
    ('aggancio', 'Aggancio barra', '6 (2 per numero)', 'Stampare in piedi. Numero 1, 2 o 3 inciso sulla faccia anteriore.'),
    ('distanziale_24', 'Distanziale 24 mm', '2', 'Sotto l\'aggancio 1.'),
    ('distanziale_50', 'Distanziale 50 mm', '4', 'Tra un aggancio e l\'altro.'),
    ('distanziale_44', 'Distanziale 44 mm', '2', 'Sopra l\'aggancio 3, bloccato dal tappo.'),
    ('tappo', 'Tappo del montante', '2', 'Stampare capovolto. Vite M5 svasata nel foro assiale.'),
    ('copertura', 'Copertura circuito barra', '3', 'Stampare capovolta. Lascia libero il connettore KK.'),
    ('culla_laterale', 'Culla laterale (modulo scheda)', '2 (una specchiata)', '2 inserti M3 per i distanziali, 2 fori a goccia per i pomelli M4.'),
    ('ponte_centrale', 'Ponte centrale (modulo scheda)', '1', '4 inserti M3 per i distanziali della scheda.'),
    ('scatola_calcolo', 'Scatola modulo di calcolo', '1', 'Dorso sul piatto. Inserti M2,5 per il Pi e M3 per il coperchio.'),
    ('coperchio_calcolo', 'Coperchio modulo di calcolo', '1', 'Faccia esterna sul piatto. Griglia ventola e finestra GPIO.'),
    ('cuffia_gpio', 'Cuffia connettore GPIO', '1', 'Faccia superiore sul piatto.'),
]
TITLE = 'MuLab · Rivelatore di muoni a tre barre'


def page():
    return Image.new('RGB', A4, 'white')


def header(im, title, sub=None, n=None, total=None):
    d = ImageDraw.Draw(im)
    d.text((mm(12), mm(9)), title, font=f(6.5, True), fill=INK)
    if sub:
        d.text((mm(12), mm(18)), sub, font=f(3.6), fill=GREY)
    d.line((mm(12), mm(24), A4[0] - mm(12), mm(24)), fill=ACCENT, width=mm(0.6))
    foot = f'{TITLE}   ·   {date.today().strftime("%d/%m/%Y")}'
    if n:
        foot += f'   ·   pagina {n} di {total}'
    d.text((mm(12), A4[1] - mm(9)), foot, font=f(2.8), fill=GREY)


def fit(img, box_w, box_h):
    r = min(box_w / img.width, box_h / img.height)
    return img.resize((max(1, round(img.width * r)), max(1, round(img.height * r))), Image.LANCZOS)


def image_page(path, title, sub, n, total):
    im = page()
    header(im, title, sub, n, total)
    src = Image.open(path).convert('RGB')
    s = fit(src, A4[0] - mm(24), A4[1] - mm(40))
    im.paste(s, ((A4[0] - s.width) // 2, mm(28) + (A4[1] - mm(40) - s.height) // 2))
    return im


def arrow(d, p0, p1, w):
    import math
    d.line((p0, p1), fill=INK, width=w)
    for a, b in ((p0, p1), (p1, p0)):
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        L, sp = mm(2.2), 0.35
        pts = [b, (b[0] - L * math.cos(ang - sp), b[1] - L * math.sin(ang - sp)),
               (b[0] - L * math.cos(ang + sp), b[1] - L * math.sin(ang + sp))]
        d.polygon(pts, fill=INK)


def dim_h(d, x0, x1, y, yref, value, above=True):
    """horizontal dimension between x0 and x1, dimension line at y, extension lines from yref"""
    w = mm(0.18)
    d.line((x0, yref, x0, y + (-mm(1.5) if above else mm(1.5))), fill=INK, width=w)
    d.line((x1, yref, x1, y + (-mm(1.5) if above else mm(1.5))), fill=INK, width=w)
    arrow(d, (x0, y), (x1, y), w)
    t = f'{value:.1f}'.rstrip('0').rstrip('.').replace('.', ',')
    ft = f(3.0)
    tw = d.textlength(t, font=ft)
    d.text(((x0 + x1) / 2 - tw / 2, y - mm(4.6)), t, font=ft, fill=INK)


def dim_v(d, y0, y1, x, xref, value):
    w = mm(0.18)
    d.line((xref, y0, x - mm(1.5), y0), fill=INK, width=w)
    d.line((xref, y1, x - mm(1.5), y1), fill=INK, width=w)
    arrow(d, (x, y0), (x, y1), w)
    t = f'{value:.1f}'.rstrip('0').rstrip('.').replace('.', ',')
    ft = f(3.0)
    txt = Image.new('RGBA', (round(d.textlength(t, font=ft)) + 4, mm(4)), (255, 255, 255, 0))
    ImageDraw.Draw(txt).text((2, 0), t, font=ft, fill=INK)
    txt = txt.rotate(90, expand=True)
    return txt, (round(x - mm(4.8)), round((y0 + y1) / 2 - txt.height / 2))


def drawing_page(stem, name, qty, notes, views_dir, parts_dir, n, total):
    info = json.load(open(os.path.join(views_dir, stem + '.json')))
    sx, sy, sz = info['size']
    sc = info['scale']
    im = page()
    header(im, f'Tavola: {name}', 'Viste ortogonali in proiezione europea (primo diedro). Quote d\'ingombro in mm.', n, total)
    d = ImageDraw.Draw(im)
    # frame
    d.rectangle((mm(10), mm(27), A4[0] - mm(10), A4[1] - mm(13)), outline=INK, width=mm(0.35))
    V = {k: Image.open(os.path.join(views_dir, f'{stem}_{k}.png')).convert('RGB') for k in ('front', 'top', 'left')}
    m = 3.0 * sc                      # render margin on paper (mm)
    g = mm(16)
    x0, y0 = mm(30), mm(50)
    fr, tp, lf = V['front'], V['top'], V['left']
    im.paste(fr, (x0, y0))
    im.paste(lf, (x0 + fr.width + g, y0))
    im.paste(tp, (x0, y0 + fr.height + g))
    # labels
    for lbl, (px, py) in (('Vista frontale', (x0, y0)), ('Vista laterale sinistra', (x0 + fr.width + g, y0)),
                          ('Vista dall\'alto', (x0, y0 + fr.height + g))):
        d.text((px + mm(m), py - mm(3.2)), lbl, font=f(2.6), fill=GREY)
    # dimensions (part edges inside each view = margin m)
    L, R = x0 + mm(m), x0 + fr.width - mm(m)
    T, B = y0 + mm(m), y0 + fr.height - mm(m)
    dim_h(d, L, R, y0 - mm(7) - mm(3.2), T, sx)
    txt, pos = dim_v(d, T, B, x0 - mm(7), L, sz)
    im.paste(txt, pos, txt)
    tT, tB = y0 + fr.height + g + mm(m), y0 + fr.height + g + tp.height - mm(m)
    txt, pos = dim_v(d, tT, tB, x0 - mm(7), L, sy)
    im.paste(txt, pos, txt)
    lL, lR = x0 + fr.width + g + mm(m), x0 + fr.width + g + lf.width - mm(m)
    dim_h(d, lL, lR, B + mm(9), B, sy, above=False)
    # title block
    tb_w, tb_h = mm(118), mm(40)
    tx, ty = A4[0] - mm(10) - tb_w, A4[1] - mm(13) - tb_h
    d.rectangle((tx, ty, tx + tb_w, ty + tb_h), outline=INK, width=mm(0.35))
    rows = [('Pezzo', name), ('File', f'pezzi/{stem}.stl'), ('Quantità', qty),
            ('Materiale', 'PETG, 4 pareti, strato 0,2 mm'),
            ('Scala', ('1:1' if sc == 1 else (f'{int(sc)}:1' if sc > 1 else f'1:{int(round(1 / sc))}')) + '  (stampare al 100%)'),
            ('Ingombro', (f'{sx:.1f} × {sy:.1f} × {sz:.1f} mm').replace('.', ',') + ' (orientamento di stampa)')]
    rh = tb_h / len(rows)
    for i, (k, v) in enumerate(rows):
        yy = ty + i * rh
        if i:
            d.line((tx, yy, tx + tb_w, yy), fill=INK, width=mm(0.15))
        d.text((tx + mm(2), yy + mm(1.4)), k, font=f(2.4), fill=GREY)
        d.text((tx + mm(24), yy + mm(1.1)), v, font=f(2.9, i == 0), fill=INK)
    d.line((tx + mm(22), ty, tx + mm(22), ty + tb_h), fill=INK, width=mm(0.15))
    # axonometric render + notes, in the free area above the title block
    iso_path = os.path.join(parts_dir, stem + '_c.png') if os.path.exists(os.path.join(parts_dir, stem + '_c.png')) else None
    free_x0 = x0 + fr.width + g
    free_y0 = y0 + max(fr.height, lf.height) + mm(16)
    free_w = A4[0] - mm(14) - free_x0
    free_h = ty - mm(10) - free_y0
    if iso_path and free_w > mm(40) and free_h > mm(30):
        iso = fit(Image.open(iso_path).convert('RGB'), free_w, free_h)
        im.paste(iso, (A4[0] - mm(12) - iso.width, ty - mm(4) - iso.height))
        d.text((A4[0] - mm(12) - iso.width, ty - mm(4) - iso.height - mm(3.6)), 'Assonometria (come va sul piatto)', font=f(2.6), fill=GREY)
    d.text((tx, ty - mm(7.5) if not iso_path else A4[1] - mm(13) + mm(1.2)), '', font=f(2.4), fill=GREY)
    # scale bar (10 mm at this scale)
    bx, by = mm(14), A4[1] - mm(19)
    d.rectangle((bx, by, bx + mm(10 * sc), by + mm(1.2)), fill=INK)
    d.text((bx + mm(10 * sc) + mm(2), by - mm(1.2)), f'10 mm   ·   {notes}', font=f(2.6), fill=INK)
    return im


def part_page(stem, name, qty, notes, parts_dir, n, total):
    im = page()
    header(im, name, f'Quantità: {qty}   ·   {notes}', n, total)
    src = Image.open(os.path.join(parts_dir, stem + '_c.png')).convert('RGB')
    s = fit(src, A4[0] - mm(24), A4[1] - mm(42))
    im.paste(s, ((A4[0] - s.width) // 2, mm(28) + (A4[1] - mm(42) - s.height) // 2))
    return im


def cover(path, n, total):
    im = page()
    d = ImageDraw.Draw(im)
    src = Image.open(path).convert('RGB')
    s = fit(src, mm(190), mm(170))
    im.paste(s, (A4[0] - mm(10) - s.width, (A4[1] - s.height) // 2))
    d.text((mm(16), mm(40)), 'MuLab', font=f(16, True), fill=INK)
    d.text((mm(16), mm(60)), 'Rivelatore di muoni', font=f(7), fill=INK)
    d.text((mm(16), mm(70)), 'a tre barre di scintillatore', font=f(7), fill=INK)
    d.line((mm(16), mm(84), mm(80), mm(84)), fill=ACCENT, width=mm(1.0))
    y = mm(92)
    for line in ('Telaio, modulo scheda, modulo di calcolo', 'Render, esploso e tavole dei pezzi stampati',
                 '', 'Stampa: A4 orizzontale, scala 100%', f'{date.today().strftime("%d/%m/%Y")}'):
        d.text((mm(16), y), line, font=f(3.6), fill=GREY)
        y += mm(6)
    return im


def main(rdir, pdir, vdir, out):
    overview = [
        ('prototipo_v12_assembled.png', 'Vista completa', 'Telaio Bosch 20×20, tre barre, modulo scheda staccabile, modulo di calcolo'),
        ('prototipo_v12_exploded.png', 'Esploso', 'Tutti i componenti; modulo scheda e modulo di calcolo si staccano in blocco'),
        ('prototipo_v12_board.png', 'Modulo scheda', 'Culle avvitate ai piedi con pomelli M4, distanziali in ottone, LEMO verso l\'esterno'),
        ('prototipo_v12_compute_open.png', 'Modulo di calcolo', 'Pi Zero 2 W su distanziali in ottone, ventola sotto il coperchio, cablaggio GPIO'),
    ]
    overview = [o for o in overview if os.path.exists(os.path.join(rdir, o[0]))]
    parts = [p for p in PARTS if os.path.exists(os.path.join(vdir, p[0] + '.json'))]
    total = 1 + len(overview) + 2 * len(parts)
    pages = [cover(os.path.join(rdir, overview[0][0]), 1, total)]
    n = 2
    for fn, t, sub in overview:
        pages.append(image_page(os.path.join(rdir, fn), t, sub, n, total)); n += 1
    for stem, name, qty, notes in parts:
        if os.path.exists(os.path.join(pdir, stem + '_c.png')):
            pages.append(part_page(stem, name, qty, notes, pdir, n, total)); n += 1
    for stem, name, qty, notes in parts:
        pages.append(drawing_page(stem, name, qty, notes, vdir, pdir, n, total)); n += 1
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=DPI, quality=92)
    print(out, len(pages), 'pagine')


if __name__ == '__main__':
    main(*sys.argv[1:5])
