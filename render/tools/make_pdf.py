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
    ('aggancio_2', 'Aggancio barra', '6: 2 × aggancio_1, 2 × aggancio_2, 2 × aggancio_3', 'Stampare in piedi. I tre file differiscono solo per il numero inciso.'),
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
    s = fit(src, mm(168), mm(160))
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


def foot_holes_page(views_dir, n, total):
    """Piede: faces with the screw holes, positions and sizes dimensioned (1:1)."""
    info = json.load(open(os.path.join(views_dir, 'piede.json')))
    sx, sy, sz = info['size']
    sc = info['scale']
    k = PX * sc
    m = 3.0
    im = page()
    header(im, 'Tavola: Piede, forature', 'Faccia interna (inserti M4 per le culle) e faccia inferiore (viti M5, gommini). Quote in mm.', n, total)
    d = ImageDraw.Draw(im)
    d.rectangle((mm(10), mm(27), A4[0] - mm(10), A4[1] - mm(13)), outline=INK, width=mm(0.35))
    bk = Image.open(os.path.join(views_dir, 'piede_back.png')).convert('RGB')
    bt = Image.open(os.path.join(views_dir, 'piede_bottom.png')).convert('RGB')
    xa, ya = mm(40), mm(44)
    yb = ya + bk.height + mm(30)
    im.paste(bk, (xa, ya))
    im.paste(bt, (xa, yb))
    d.text((xa + mm(m), ya - mm(4)), 'Faccia interna (verso la traversa), vista di fronte', font=f(2.8, True), fill=INK)
    d.text((xa + mm(m), yb - mm(4)), 'Faccia inferiore (sul tavolo), vista da sotto', font=f(2.8, True), fill=INK)

    def P(view, u, v):          # part coords (u right, v up, centred) -> page px
        W, H = (sx + 2 * m), (sz + 2 * m) if view == 'back' else (sy + 2 * m)
        x0, y0 = (xa, ya) if view == 'back' else (xa, yb)
        return x0 + (u + W / 2) * k, y0 + (H / 2 - v) * k

    zc = sz / 2
    # --- inner face: 4 insert holes at y = +-28 (z 8) and +-50 (z 4.4)
    bl = P('back', -sx / 2, -zc)[1]
    for u, z in ((-50, 4.4), (-28, 8.0), (28, 8.0), (50, 4.4)):
        cx, cy = P('back', u, z - zc)
        d.line((cx, cy - mm(4), cx, bl + mm(18)), fill=ACCENT, width=mm(0.15))
    y1 = bl + mm(10)
    dim_h(d, *[P('back', u, 0)[0] for u in (-28, 28)], y1, bl, 56, above=False)
    dim_h(d, *[P('back', u, 0)[0] for u in (-50, 50)], y1 + mm(9), bl, 100, above=False)
    xr = P('back', sx / 2, 0)[0] + mm(10)
    for z, dx in ((8.0, 0), (4.4, mm(13))):
        cy = P('back', 0, z - zc)[1]
        txt, pos = dim_v(d, cy, bl, xr + dx, P('back', 50 if z < 5 else 28, 0)[0], z)
        im.paste(txt, pos, txt)
    cx, cy = P('back', 50, 4.4 - zc)
    d.line((cx, cy, cx + mm(30), cy - mm(16)), fill=INK, width=mm(0.18))
    d.text((cx + mm(31), cy - mm(19)), '4× Ø5,6 prof. 10 (foro a goccia)\ninserto a caldo M4 × 8,1\n2 per lato: piede reversibile', font=f(2.7), fill=INK)
    # --- bottom face: M5 for the upright (30 from the inner face), M5 for the cross-member (9), pads
    top_edge = P('bottom', 0, sy / 2)[1]
    for v_in, lab, ofs in ((30.0, 'Ø5,5 passante, lamatura Ø9,5 × 5\nvite M5×16 nel montante', 0),
                           (9.0, 'Ø5,5 passante, lamatura Ø10,2 × 3\nvite M5×8 nel dado a T della traversa', 1)):
        v = sy / 2 - v_in - 0.4
        cx, cy = P('bottom', 0, v)
        lx = P('bottom', sx / 2, 0)[0] + mm(8)
        ly = P('bottom', 0, sy / 2)[1] + mm(2 + 16 * (1 - ofs))
        d.line((cx, cy, lx - mm(1), ly + mm(2.5)), fill=INK, width=mm(0.18))
        d.text((lx, ly), lab, font=f(2.7), fill=INK)
        xl = P('bottom', -sx / 2, 0)[0] - mm(8 + 9 * ofs)
        txt, pos = dim_v(d, top_edge, cy, xl, cx, v_in)
        im.paste(txt, pos, txt)
    bb = P('bottom', 0, -sy / 2)[1]
    vp = sy / 2 - 30.0 - 0.4
    dim_h(d, P('bottom', -60, vp)[0], P('bottom', 60, vp)[0], bb + mm(10), bb, 120, above=False)
    cx, cy = P('bottom', 60, vp)
    lx = P('bottom', sx / 2, 0)[0] + mm(8)
    ly = P('bottom', 0, sy / 2)[1] + mm(36)
    d.line((cx, cy, lx - mm(1), ly + mm(2.5)), fill=INK, width=mm(0.18))
    d.text((lx, ly), '2× Ø12,6 × 1\ngommino adesivo Ø12', font=f(2.7), fill=INK)
    d.text((mm(14), A4[1] - mm(19)), 'Scala 1:1 (stampare al 100%). I fori degli inserti sono a goccia per stamparli senza supporti: '
           'l\'inserto, scaldato, riempie la punta.', font=f(2.6), fill=INK)
    return im


def inserts_page(n, total):
    im = page()
    header(im, 'Inserti filettati a caldo', 'Come si montano, e dove vanno', n, total)
    d = ImageDraw.Draw(im)
    x, y = mm(14), mm(32)
    steps = [
        'Serve: saldatore regolabile da almeno 60 W con punta per inserti (kit M2,5 / M3 / M4), inserti corti tipo Ruthex o CNC Kitchen,',
        'una piastrina metallica piatta. Lavoro da laboratorio: in classe arrivano i pezzi con gli inserti già montati.',
        '',
        '1.  Saldatore a circa 240 °C per il PETG (210–220 °C per il PLA).',
        '2.  Foro in verticale: i piedi vanno appoggiati sul fianco, perché i fori M4 sono orizzontali.',
        '3.  Inserto appoggiato dritto sul foro, lato stretto in basso.',
        '4.  Punta dentro l\'inserto, pressione leggera e in asse: scende in 3–5 secondi. Non spingere forte e non ruotare.',
        '5.  Fermarsi a 0,5 mm dal filo, togliere il saldatore e premere subito la piastrina finché la plastica si raffredda.',
        '6.  Pulire i fili di plastica e provare la vite a pezzo freddo. Un inserto storto si riscalda e si estrae.',
        '',
        'Gli inserti delle culle e del ponte reggono la scheda: controllare che siano dritti usando la scheda stessa come dima.',
    ]
    for t in steps:
        d.text((x, y), t, font=f(3.1), fill=INK)
        y += mm(5.6)
    y += mm(4)
    rows = [('Inserto', 'Ø foro', 'Prof.', 'Q.tà', 'Dove'),
            ('M4 × 8,1', '5,6', '10', '8', 'piedi, fianco interno: 4 per piede (si usano i 2 anteriori), per i pomelli delle culle'),
            ('M3 × 5,7', '4,0', '6', '4', 'culle laterali: 2 per culla, sotto i distanziali della scheda'),
            ('M3 × 5,7', '4,0', '6', '4', 'ponte centrale, sotto i distanziali della scheda'),
            ('M3 × 5,7', '4,0', '7', '3', 'scatola del modulo di calcolo, viti del coperchio'),
            ('M2,5 × 4', '3,6', '5', '4', 'scatola del modulo di calcolo, distanziali del Pi Zero 2 W')]
    cols = [mm(14), mm(44), mm(66), mm(84), mm(100)]
    for i, r in enumerate(rows):
        for c, t in zip(cols, r):
            d.text((c, y), t, font=f(3.1, i == 0), fill=INK)
        y += mm(7)
        d.line((mm(14), y - mm(1.5), A4[0] - mm(14), y - mm(1.5)), fill=GREY if i else INK, width=mm(0.15 if i else 0.3))
    return im


def main(rdir, pdir, vdir, out):
    overview = [
        ('prototipo_v13_assembled.png', 'Vista completa', 'Telaio Bosch 20×20, tre barre, modulo scheda staccabile, modulo di calcolo'),
        ('prototipo_v13_exploded.png', 'Esploso', 'Tutti i componenti; modulo scheda e modulo di calcolo si staccano in blocco'),
        ('prototipo_v13_board.png', 'Modulo scheda', 'Culle avvitate ai piedi con pomelli M4, distanziali in ottone, LEMO verso l\'esterno'),
        ('prototipo_v13_cavi.png', 'Cablaggio', 'Coassiali barra → scheda (KK), LEMO → GPIO del Pi, I²C da J6, 5 V a J3 dal retro, alimentazione del Pi'),
        ('prototipo_v13_cavi_dettaglio.png', 'Cablaggio, dettaglio', 'J3 (5 V) sul bordo posteriore, J6 (I²C) e uscite LEMO sul bordo anteriore, cuffia GPIO sul modulo di calcolo'),
        ('prototipo_v13_compute_open.png', 'Modulo di calcolo', 'Pi Zero 2 W su distanziali in ottone, ventola sotto il coperchio, cablaggio GPIO'),
    ]
    overview = [o for o in overview if os.path.exists(os.path.join(rdir, o[0]))]
    parts = [p for p in PARTS if os.path.exists(os.path.join(vdir, p[0] + '.json'))]
    extra = os.path.exists(os.path.join(vdir, 'piede_back.png'))
    total = 1 + len(overview) + 2 * len(parts) + 1 + (1 if extra else 0)
    pages = [cover(os.path.join(rdir, overview[0][0]), 1, total)]
    n = 2
    for fn, t, sub in overview:
        pages.append(image_page(os.path.join(rdir, fn), t, sub, n, total)); n += 1
    for stem, name, qty, notes in parts:
        if os.path.exists(os.path.join(pdir, stem + '_c.png')):
            pages.append(part_page(stem, name, qty, notes, pdir, n, total)); n += 1
    for stem, name, qty, notes in parts:
        pages.append(drawing_page(stem, name, qty, notes, vdir, pdir, n, total)); n += 1
        if stem == 'piede' and extra:
            pages.append(foot_holes_page(vdir, n, total)); n += 1
    pages.append(inserts_page(n, total)); n += 1
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=DPI, quality=92)
    print(out, len(pages), 'pagine')


if __name__ == '__main__':
    main(*sys.argv[1:5])
