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
PANEL_TOP = 520.0       # bordo superiore -> fori della 1a riga a 80 mm dal bordo (tavola centrata in altezza)
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

# Sul plexi il blocco f e' sfalsato di 60 mm rispetto alle colonne del corpo:
# nessun taglio dritto lo eviterebbe. Sul legno lo spostiamo di 60 mm a sinistra,
# allineandolo sotto i gruppi 3-17 (La sotto Sc/Y), cosi' un solo taglio dritto basta.
F_SHIFT = -60.0
holes = [(x + (F_SHIFT if round(y, 3) in (-495.0, -620.0) else 0.0), y, r) for x, y, r in holes]

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
            col = round((xc + 775 - F_SHIFT) / 125) + 1
        cubes.append((element_at(ri, col), ri, xc, ry, [a, b]))
assert sorted(c[0] for c in cubes) == list(range(1, 119))

CUBE = 120.0

def side_of(x, y):
    return "A" if x < SEAM_X else "B"

# controllo: nessun cubo (120 mm) attraversa il taglio
for Z, ri, xc, yc, hs in cubes:
    assert not (xc - CUBE / 2 < SEAM_X < xc + CUBE / 2), SYMS[Z - 1]

# --- disegno ----------------------------------------------------------------
def make(name, side):
    x0 = PLEXI_L if side == "A" else SEAM_X
    x1 = x0 + PANEL_W
    W = PANEL_W
    c = canvas.Canvas(name, pagesize=((W + 2 * MARGIN) * mm, (PANEL_H + 2 * MARGIN) * mm))
    c.setTitle(f"Dima foratura pannello {side} - scala 1:1")
    P = lambda x, y: ((x - x0 + MARGIN) * mm, (y - PANEL_BOT + MARGIN) * mm)
    mine = [cb for cb in cubes if side_of(cb[2], cb[3]) == side]
    allh = [h for cb in mine for h in cb[4]]

    c.setLineWidth(0.6)
    c.rect(MARGIN * mm, MARGIN * mm, W * mm, PANEL_H * mm)
    c.setLineWidth(2.5)
    c.line(*P(x0, PANEL_TOP), *P(x1, PANEL_TOP))
    c.line(*P(SEAM_X, PANEL_BOT), *P(SEAM_X, PANEL_TOP))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(*P((x0 + x1) / 2, PANEL_TOP - 14), "^ BORDO ALTO - riferimento ^")
    sx, sy = P(SEAM_X + (-14 if side == "A" else 14), PANEL_BOT + PANEL_H / 2)
    c.saveState(); c.translate(sx, sy); c.rotate(90 if side == "A" else -90)
    c.drawCentredString(0, -2 * mm, "BORDO DI GIUNZIONE - riferimento (accostare all'altro pannello)")
    c.restoreState()

    # ingombro presunto dei cubi (tratteggio leggero) + fori
    for Z, ri, xc, yc, hs in mine:
        c.setLineWidth(0.3); c.setDash(3, 3); c.setStrokeGray(0.55)
        top = yc + CUBE / 2
        c.rect(*P(xc - CUBE / 2, top - CUBE), CUBE * mm, CUBE * mm)
        c.setDash(); c.setStrokeGray(0)
        for hx, hy, r in hs:
            px, py = P(hx, hy)
            c.setLineWidth(0.25)
            c.line(px - 8 * mm, py, px + 8 * mm, py)
            c.line(px, py - 8 * mm, px, py + 8 * mm)
            c.setLineWidth(0.5)
            c.circle(px, py, r * mm)
            c.circle(px, py, 0.5 * mm, fill=1)
        lx, ly = P(xc, yc)
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(lx, ly - 14 * mm, SYMS[Z - 1])
        c.setFont("Helvetica", 11)
        c.drawCentredString(lx, ly + 10 * mm, str(Z))

    def txt(x, y, s, size=18, bold=False):
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(*P(x, y), s)

    tx, ty = (-880, 470) if side == "A" else (20, 320)
    other = "B (destro)" if side == "A" else "A (sinistro)"
    lines = [
        (f"DIMA PANNELLO {side} - {'SINISTRO' if side=='A' else 'DESTRO'}", 26, True),
        ("vista frontale (lato su cui vanno i cubi)", 16, False),
        ("STAMPA IN SCALA 1:1 - 100% - NON 'adatta alla pagina'", 18, True),
        (f"Pannello 1250 x 1250 mm. Fori Ø4.5 mm: {len(allh)}  ({len(mine)} cubi)", 16, False),
        ("Rifilare la carta sulla linea del contorno.", 16, False),
        ("Allineare sui 2 bordi spessi: ALTO + GIUNZIONE.", 16, False),
        (f"La giunzione va accostata al pannello {other}.", 16, False),
        ("Taglio dritto tra gruppo 9 e 10: nessun cubo diviso.", 16, False),
        ("Tratteggio grigio = ingombro cubo (indicativo).", 16, False),
    ]
    yy = ty
    for s_, sz, b in lines:
        txt(tx, yy, s_, sz, b); yy -= sz * 0.353 * 1.7 + 4
    if side == "A":
        qx, qy = -880, yy - 115
        c.setLineWidth(0.5)
        c.rect(*P(qx, qy), 100 * mm, 100 * mm)
        txt(qx + 110, qy + 45, "Controllo: questo quadrato deve misurare 100 x 100 mm", 14)
    else:
        bx, by = 60, 420
        c.setLineWidth(1.0)
        c.line(*P(bx, by), *P(bx + 500, by))
        for k in range(0, 501, 100):
            c.line(*P(bx + k, by - 6), *P(bx + k, by + 6))
        txt(bx, by + 12, "Controllo: barra = 500 mm (tacche ogni 100 mm)", 14)

    row4 = [h for h in allh if abs(h[1] - 65) < 1e-6]
    xmin, xmax = min(h[0] for h in row4), max(h[0] for h in row4)
    c.setLineWidth(0.3); c.setDash(4, 3)
    c.line(*P(xmin, 30), *P(xmax, 30)); c.setDash()
    c.setFont("Helvetica", 12)
    c.drawCentredString(*P((xmin + xmax) / 2, 33),
                        f"VERIFICA dopo la stampa: {xmax - xmin:.1f} mm tra il primo e l'ultimo foro di questa riga")
    ox = (min if side == "A" else max)(h[0] for h in allh)
    oy = [h[1] for h in allh if abs(h[0] - ox) < 1e-6]
    c.drawString(*P(x0 + 40 if side == "A" else x1 - 420, PANEL_BOT + 15),
                 f"VERIFICA: 1a riga fori a {PANEL_TOP - 440:.1f} mm dal bordo alto; colonna esterna: "
                 f"{max(oy) - min(oy):.1f} mm tra primo e ultimo foro")
    c.save()
    return len(allh), len(mine), W

for nm, sd in (("dima_pannello_A_sinistro.pdf", "A"), ("dima_pannello_B_destro.pdf", "B")):
    print(sd, make(nm, sd))

# riepilogo quote (coordinate dal bordo ALTO e dal bordo di GIUNZIONE)
with open("quote_fori.csv", "w") as f:
    f.write("pannello,Z,simbolo,x_da_giunzione_mm(+ verso destra),dist_da_alto_mm\n")
    for Z, ri, xc, yc, hs in sorted(cubes):
        for hx, hy, r in hs:
            sd = side_of(hx, hy)
            f.write(f"{sd},{Z},{SYMS[Z-1]},{hx - SEAM_X:.1f},{PANEL_TOP - hy:.1f}\n")
print("ok")
