"""Rastrelliera per 5 flaconi Ø40 x 70 mm — Creality K2, PETG-CF.
Genera gli STL con manifold3d:  pip install manifold3d numpy
"""
import math
import numpy as np
from manifold3d import Manifold, CrossSection, JoinType, FillRule

# ---------------- parametri (mm) ----------------
D_FLACONE = 40.0
GIOCO     = 1.0          # gioco radiale -> foro Ø42
D_FORO    = D_FLACONE + 2 * GIOCO   # 41
PASSO     = 46.0         # interasse fori -> parete di 5 mm tra i fori
BORDO     = 4.0          # parete esterna minima
H         = 26.0         # altezza rastrelliera
FONDO     = 2.0          # fondo -> tasca profonda 24 mm (~34% del flacone)
R_ANGOLI  = 8.0          # raggio angoli esterni
SMUSSO    = 1.2          # smusso spigolo superiore esterno
INVITO    = 1.5          # smusso d'invito sul bordo dei fori
PIEDE     = 0.6          # smusso anti-"zampa d'elefante" alla base
TACCA_L   = 20.0         # larghezza tacca frontale (presa / etichetta)
TACCA_P   = 13.0         # profondità tacca dall'alto
D_FORO_FONDO = 26.0      # foro grande nel fondo: meno materiale, si spinge fuori il flacone
SEG = 128

# ---------------- scritte bicolore (CFS) ----------------
ETICHETTE = ["Li", "Na", "Cu", "B", "K"]   # una per foro, da sinistra a destra
FASCIA    = 12.0         # gradino frontale su cui stanno le scritte (versione in fila)
H_FASCIA  = 12.0         # altezza del gradino (basso = meno materiale)
H_TESTO   = 7.0          # altezza delle maiuscole
INCASSO   = 0.6          # profondità scritta = 3 layer da 0,2 -> pochi cambi colore
FONT      = "DejaVu Sans"

def blocco_arrotondato(w, d, H=H):
    """Parallelepipedo w x d x H con angoli raggiati, smusso sopra e alla base."""
    def sez(off):
        base = CrossSection.square((w - 2 * R_ANGOLI, d - 2 * R_ANGOLI), center=True)
        return base.offset(R_ANGOLI - off, JoinType.Round, circular_segments=SEG)
    corpo = Manifold.extrude(sez(0), H - SMUSSO - PIEDE).translate((0, 0, PIEDE))
    top   = Manifold.extrude(sez(SMUSSO), 0.01).translate((0, 0, H - 0.01))
    bot   = Manifold.extrude(sez(PIEDE), 0.01)
    return Manifold.batch_hull([corpo, top]) + Manifold.batch_hull([corpo, bot])

def tasca(x, y, d_bordo, tacca=True):
    """Foro per un flacone; tacca verso il bordo frontale (y negativa) a distanza d_bordo."""
    r = D_FORO / 2
    t = Manifold.cylinder(H, r, r, SEG).translate((x, y, FONDO))
    t += Manifold.cylinder(INVITO + 0.01, r, r + INVITO, SEG).translate((x, y, H - INVITO))
    t += Manifold.cylinder(H, D_FORO_FONDO / 2, D_FORO_FONDO / 2, 64).translate((x, y, -1))
    if tacca:
        rt = TACCA_L / 2
        z0 = H - TACCA_P + rt                      # fondo tacca arrotondato a U
        box = Manifold.cube((TACCA_L, d_bordo + 2, H), center=False).translate(
            (x - rt, y - d_bordo - 1, z0))
        cil = Manifold.cylinder(d_bordo + 2, rt, rt, SEG).rotate((-90, 0, 0)).translate(
            (x, y - d_bordo - 1, z0))
        t += box + cil
    return t

def testo(s, x, y):
    """Scritta s centrata in (x, y), come CrossSection, alta H_TESTO (maiuscole)."""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    fp = FontProperties(family=FONT, weight="bold")
    cap = TextPath((0, 0), "H", size=1, prop=fp).get_extents().height
    tp = TextPath((0, 0), s, size=H_TESTO / cap, prop=fp)
    polys = [p for p in tp.to_polygons(closed_only=True) if len(p) > 2]
    cs = CrossSection(polys, FillRule.EvenOdd)
    (x0, y0), (x1, y1) = cs.bounds()[:2], cs.bounds()[2:]
    return cs.translate((x - (x0 + x1) / 2, y - (y0 + y1) / 2))

def fila_scritte():
    """Versione in fila con fascia frontale e scritte incassate. Ritorna (base, scritte)."""
    w = 4 * PASSO + D_FORO + 2 * BORDO
    d_corpo = D_FORO + 2 * BORDO
    d = d_corpo + FASCIA
    corpo = blocco_arrotondato(w, d_corpo).translate((0, FASCIA / 2, 0))
    gradino = blocco_arrotondato(w, d, H_FASCIA)
    m = corpo + gradino
    y_foro = FASCIA / 2
    y_testo = (-d / 2 + SMUSSO + y_foro - d_corpo / 2) / 2
    z_top = H_FASCIA
    scritte = Manifold()
    for i in range(5):
        m -= tasca((i - 2) * PASSO, y_foro, 0, tacca=False)
        scritte += Manifold.extrude(testo(ETICHETTE[i], (i - 2) * PASSO, y_testo), INCASSO).translate(
            (0, 0, z_top - INCASSO))
    return m - scritte, scritte

def fila():
    w = 4 * PASSO + D_FORO + 2 * BORDO
    d = D_FORO + 2 * BORDO
    m = blocco_arrotondato(w, d)
    for i in range(5):
        m -= tasca((i - 2) * PASSO, 0, d / 2)
    return m

def sfalsata():
    dy = math.sqrt(PASSO**2 - (PASSO / 2) ** 2)    # file a 60°
    w = 2 * PASSO + D_FORO + 2 * BORDO
    d = dy + D_FORO + 2 * BORDO
    m = blocco_arrotondato(w, d)
    for i in range(3):                              # fila posteriore: 3
        m -= tasca((i - 1) * PASSO, dy / 2, 0, tacca=False)
    for i in range(2):                              # fila anteriore: 2, con tacca
        m -= tasca((i - 0.5) * PASSO, -dy / 2, d / 2 - dy / 2)
    return m

def to_tm(m):
    import trimesh
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts))

def salva(m, nome):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    f = np.asarray(mesh.tri_verts)
    import trimesh
    tm = trimesh.Trimesh(v, f)
    tm.export(nome)
    b = tm.bounds
    print(f"{nome}: {b[1]-b[0]} mm, volume {tm.volume/1000:.1f} cm³, watertight={tm.is_watertight}")
    return tm

if __name__ == "__main__":
    salva(fila(), "rastrelliera_5_fila.stl")
    salva(sfalsata(), "rastrelliera_5_sfalsata.stl")
    base, scritte = fila_scritte()
    salva(base, "rastrelliera_5_scritte_BASE.stl")
    salva(scritte, "rastrelliera_5_scritte_TESTO.stl")
    import trimesh
    sc = trimesh.Scene()
    sc.add_geometry(to_tm(base), node_name="base", geom_name="base")
    sc.add_geometry(to_tm(scritte), node_name="scritte", geom_name="scritte")
    sc.export("rastrelliera_5_scritte_bicolore.3mf")
    print("rastrelliera_5_scritte_bicolore.3mf: base + scritte")
