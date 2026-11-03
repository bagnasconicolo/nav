"""Genera le dime di foratura (scala 1:1) per i due pannelli in legno
che sostituiscono il pannello frontale in plexiglass della tavola periodica.

Uso:  python3 genera_dime.py pt_panel.dxf
Output: dima_pannello_A_sinistro.pdf, dima_pannello_B_destro.pdf
"""
import sys, collections
import ezdxf
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

DXF = sys.argv[1] if len(sys.argv) > 1 else "pt_panel.dxf"

# --- geometria del pannello in legno (coordinate del DXF, mm) -------------
SEAM_X = -22.5          # giunzione: tra il gruppo 9 e il 10 (meta' esatta del plexi 2500)
PLEXI_L, PLEXI_R = -1272.5, 1227.5
PANEL_W = 1250.0
PANEL_H = 1250.0
PANEL_TOP = 505.0       # bordo superiore -> fori della 1a riga a 65 mm dal bordo
PANEL_BOT = PANEL_TOP - PANEL_H
MARGIN = 10.0           # bianco attorno al pannello nel PDF (pagina 1270 x 1270)

SYMS = ("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn "
        "Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr "
        "Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra "
        "Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og").split()

def element_at(row, col):
    """row: 1-7 periodi, 8 lantanidi, 9 attinidi; col: 1-18 (o 1-15 per blocco f)."""
    if row == 8: return 57 + col - 1
    if row == 9: return 89 + col - 1
    if row == 1: return {1: 1, 18: 2}[col]
    if row in (2, 3):
        base = 3 if row == 2 else 11
        return base + (col - 1 if col <= 2 else col - 11)
    if row in (4, 5):
        return (19 if row == 4 else 37) + col - 1
    # periodi 6-7: gruppo 3 vuoto (La/Ac stanno nel blocco f)
    if col <= 2:
        return (55 if row == 6 else 87) + col - 1
    return (72 if row == 6 else 104) + col - 4

# verifica rapida della formula per periodi 6/7: col4 -> Hf(72)/Rf(104)
assert element_at(6, 4) == 72 and element_at(7, 18) == 118 and element_at(6, 2) == 56

# --- lettura fori dal DXF ---------------------------------------------------
doc = ezdxf.readfile(DXF)
holes = [(c.dxf.center.x, c.dxf.center.y, c.dxf.radius) for c in doc.modelspace().query("CIRCLE")]
assert len(holes) == 236, len(holes)
row_ys = sorted({round(y, 3) for _, y, _ in holes}, reverse=True)
assert len(row_ys) == 9

cubes = []   # (Z, row, xc, yc, [(x,y,r),(x,y,r)])
for ri, ry in enumerate(row_ys, start=1):
    xs = sorted((h for h in holes if round(h[1], 3) == ry), key=lambda h: h[0])
    for i in range(0, len(xs), 2):
        a, b = xs[i], xs[i + 1]
        assert abs(b[0] - a[0] - 40) < 1e-6
        xc = (a[0] + b[0]) / 2
        if ri <= 7:
            col = round((xc + 1085) / 125) + 1
        else:
            col = round((xc + 775) / 125) + 1
        cubes.append((element_at(ri, col), ri, xc, ry, [a, b]))
assert sorted(c[0] for c in cubes) == list(range(1, 119))

# --- disegno ----------------------------------------------------------------
def make(name, x0, side):
    x1 = x0 + PANEL_W
    page = PANEL_W + 2 * MARGIN
    c = canvas.Canvas(name, pagesize=(page * mm, page * mm))
    c.setTitle(f"Dima foratura pannello {side} - scala 1:1")
    P = lambda x, y: ((x - x0 + MARGIN) * mm, (y - PANEL_BOT + MARGIN) * mm)

    # contorno pannello = linea di taglio della carta
    c.setLineWidth(0.5); c.setDash()
    c.rect(MARGIN * mm, MARGIN * mm, PANEL_W * mm, PANEL_H * mm)
    # bordi di riferimento (alto + giunzione) piu' marcati
    seam_u = (SEAM_X - x0)
    c.setLineWidth(2.0)
    c.line(*P(x0, PANEL_TOP), *P(x1, PANEL_TOP))
    c.line(*P(SEAM_X, PANEL_BOT), *P(SEAM_X, PANEL_TOP))
    # etichette dei bordi di riferimento
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(*P(x0 + PANEL_W / 2, PANEL_TOP - 14), "▲ BORDO ALTO - riferimento ▲".replace("▲", "^"))
    sx, sy = P(SEAM_X + (-14 if side == "A" else 14), PANEL_BOT + PANEL_H / 2)
    c.saveState(); c.translate(sx, sy); c.rotate(90 if side == "A" else -90)
    c.drawCentredString(0, -2 * mm, "BORDO DI GIUNZIONE - riferimento (accostare all'altro pannello)")
    c.restoreState()

    # fori
    for Z, ri, xc, yc, hs in cubes:
        inside = [h for h in hs if x0 < h[0] < x1]
        if not inside:
            continue
        for hx, hy, r in inside:
            px, py = P(hx, hy)
            c.setLineWidth(0.25)
            c.line(px - 8 * mm, py, px + 8 * mm, py)
            c.line(px, py - 8 * mm, px, py + 8 * mm)
            c.setLineWidth(0.5)
            c.circle(px, py, r * mm)
            c.circle(px, py, 0.5 * mm, fill=1)
        lx, ly = P(xc, yc)
        c.setFont("Helvetica-Bold", 22)
        label = SYMS[Z - 1]
        if len(inside) == 1:   # cubo a cavallo della giunzione
            lx = P(inside[0][0], yc)[0]
            label += " (1 foro)"
            c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(lx, ly - 14 * mm, label)
        c.setFont("Helvetica", 11)
        c.drawCentredString(lx, ly + 10 * mm, str(Z))

    # testi
    def txt(x, y, s, size=18, bold=False):
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(*P(x, y), s)

    if side == "A":
        tx, ty = -880, 470          # zona vuota (gruppi 3-9, periodi 1-3)
    else:
        tx, ty = 20, 320            # zona vuota (gruppi 10-12, periodi 2-3)
    other = "B (destro)" if side == "A" else "A (sinistro)"
    lines = [
        (f"DIMA PANNELLO {side} - {'SINISTRO' if side=='A' else 'DESTRO'}", 26, True),
        ("vista frontale (lato su cui vanno i cubi)", 16, False),
        ("STAMPA IN SCALA 1:1 - 100% - NON 'adatta alla pagina'", 18, True),
        (f"Pannello 1250 x 1250 mm. Fori Ø4.5 mm: {sum(1 for cb in cubes for h in cb[4] if x0 < h[0] < x1)}", 16, False),
        ("Rifilare la carta sulla linea del contorno.", 16, False),
        ("Allineare la dima sui 2 bordi spessi: ALTO + GIUNZIONE.", 16, False),
        (f"Il bordo di giunzione va accostato al pannello {other}.", 16, False),
        ("Eu e Am stanno a cavallo: 1 foro su ogni pannello.", 16, False),
    ]
    yy = ty
    for s, sz, b in lines:
        txt(tx, yy, s, sz, b); yy -= sz * 0.353 * 1.7 + 4
    if side == "A":
        # quadrato di controllo 100 x 100 mm
        qx, qy = -880, yy - 115
        c.setLineWidth(0.5)
        c.rect(*P(qx, qy), 100 * mm, 100 * mm)
        txt(qx + 110, qy + 45, "Controllo: questo quadrato deve misurare 100 x 100 mm", 14)
    else:
        # barra di controllo 500 mm (zona vuota periodo 1, gruppi 10-17)
        bx, by = 60, 420
        c.setLineWidth(1.0)
        c.line(*P(bx, by), *P(bx + 500, by))
        for k in range(0, 501, 100):
            c.line(*P(bx + k, by - 6), *P(bx + k, by + 6))
        txt(bx, by + 12, "Controllo: barra = 500 mm (tacche ogni 100 mm)", 14)

    # quote di verifica tra fori estremi del pannello
    ins = [h for cb in cubes for h in cb[4] if x0 < h[0] < x1 and abs(h[1] - 65) < 1e-6]
    xmin, xmax = min(h[0] for h in ins), max(h[0] for h in ins)
    ymin, ymax = min(h[1] for h in ins), max(h[1] for h in ins)
    # orizzontale, lungo la riga del periodo 4 (y=65) leggermente sotto
    c.setLineWidth(0.3); c.setDash(4, 3)
    hy = 65 - 35
    c.line(*P(xmin, hy), *P(xmax, hy))
    c.setDash()
    c.setFont("Helvetica", 12)
    mx, my = P((xmin + xmax) / 2, hy + 3)
    c.drawCentredString(mx, my, f"VERIFICA dopo la stampa: {xmax - xmin:.1f} mm tra il primo e l'ultimo foro di questa riga")
    # distanze dai bordi di riferimento
    c.setFont("Helvetica", 12)
    seam_hole = max(ins, key=lambda h: h[0]) if side == "A" else min(ins, key=lambda h: h[0])
    allh = [h for cb in cubes for h in cb[4] if x0 < h[0] < x1]
    oy = [h for h in allh if abs(h[0] - (min if side == 'A' else max)(q[0] for q in allh)) < 1e-6]
    c.drawString(*P(x0 + 40 if side == "A" else x1 - 420, PANEL_BOT + 15),
                 f"VERIFICA: 1a riga fori a {PANEL_TOP - 440:.1f} mm dal bordo alto; colonna esterna: "
                 f"{max(h[1] for h in oy) - min(h[1] for h in oy):.1f} mm tra primo e ultimo foro")
    c.save()

make("dima_pannello_A_sinistro.pdf", SEAM_X - PANEL_W, "A")
make("dima_pannello_B_destro.pdf", SEAM_X, "B")

# riepilogo quote (coordinate dal bordo ALTO e dal bordo di GIUNZIONE)
with open("quote_fori.csv", "w") as f:
    f.write("pannello,Z,simbolo,dist_da_giunzione_mm,dist_da_alto_mm\n")
    for Z, ri, xc, yc, hs in sorted(cubes):
        for hx, hy, r in hs:
            side = "A" if hx < SEAM_X else "B"
            f.write(f"{side},{Z},{SYMS[Z-1]},{abs(hx - SEAM_X):.1f},{PANEL_TOP - hy:.1f}\n")
print("ok")
