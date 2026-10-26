"""Cerchietto "coltello in testa" per cane - generatore STL (PETG).

Tre pezzi stampati in piano, senza supporti:
  - cerchietto.stl : archetto con due linguette di innesto e due occhielli per l'elastico sottogola
  - lama.stl       : mezza lama (lato punta)
  - manico.stl     : tallone della lama + manico con rivetti incassati

Uso:  python3 genera.py            (richiede: pip install manifold3d trimesh numpy)
Tutte le misure sono in mm e si cambiano nella sezione PARAMETRI.
"""
import math
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, Error, FillRule, JoinType, Manifold

# ---------------------------------------------------------------- PARAMETRI
# Cerchietto (misurare la testa del cane tra le basi delle orecchie)
A_ELLISSE = 58.0      # semiasse orizzontale della linea media (larghezza interna ~ 2*A - SPESS = 112)
B_ELLISSE = 50.0      # semiasse verticale della linea media
SPESS = 4.0           # spessore radiale dell'archetto (flessibilita')
ALTEZZA = 6.0         # altezza di stampa (asse Z) dell'archetto
ANG_INIZIO = -42.0    # estremo destro dell'arco (gradi, 0 = destra, 90 = alto)
ANG_FINE = 222.0      # estremo sinistro dell'arco
OCCHIELLO_D = 11.0    # diametro esterno occhiello sottogola
FORO_D = 4.0          # foro per elastico tondo 2-3 mm

# Coltello
INCLINAZIONE = 12.0   # inclinazione dell'asse del coltello (gradi): manico in alto a destra
SP_LAMA = 4.5         # spessore lama
SP_MANICO = 6.5       # spessore manico
H_LAMA = 26.0         # altezza lama al tallone
LAMA_FUORI = 80.0     # quanto sporge la lama oltre il cerchietto
MOZZO_FUORI = 14.0    # pezzo di lama visibile lato manico prima del manico
L_MANICO = 72.0       # lunghezza manico
H_MANICO = 21.0       # altezza manico

# Innesto (linguetta sul cerchietto -> tasca nel coltello)
LING_LARG = 10.0      # larghezza linguetta
LING_LUNG = 12.0      # quanto entra nel coltello oltre il bordo del cerchietto
LING_H = 2.6          # altezza linguetta (Z), a filo col retro
GIOCO = 0.2           # gioco per lato (PETG: 0.15-0.25)
GIOCO_BORDO = 0.15    # gioco tra bordo concavo del coltello e cerchietto

SEG = 256
OUT = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- UTILITA'
def ellisse_pt(t):
    return np.array([A_ELLISSE * math.cos(t), B_ELLISSE * math.sin(t)])


def ellisse_norm(t):
    n = np.array([B_ELLISSE * math.cos(t), A_ELLISSE * math.sin(t)])
    return n / np.linalg.norm(n)


def raggio_ellisse(phi):
    """Distanza dal centro della linea media lungo la direzione phi."""
    a, b = A_ELLISSE, B_ELLISSE
    return a * b / math.hypot(b * math.cos(phi), a * math.sin(phi))


def cs(pts):
    return CrossSection([np.asarray(pts, dtype=float).tolist()], FillRule.NonZero)


def arrotonda(sez, r):
    """Raccorda gli spigoli convessi con raggio r."""
    return sez.offset(-r, JoinType.Round, 2, SEG).offset(
        r, JoinType.Round, 2, SEG)


def ruota(pts, ang):
    c, s = math.cos(ang), math.sin(ang)
    p = np.asarray(pts, dtype=float)
    return np.stack([c * p[:, 0] - s * p[:, 1], s * p[:, 0] + c * p[:, 1]], axis=1)


def rettangolo(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def esporta(man, nome):
    m = man.to_mesh()
    tm = trimesh.Trimesh(vertices=m.vert_properties[:, :3], faces=m.tri_verts, process=False)
    assert tm.is_watertight, nome
    tm.export(os.path.join(OUT, nome))
    return tm


# ---------------------------------------------------------------- CERCHIETTO
theta = math.radians(INCLINAZIONE)
t0, t1 = math.radians(ANG_INIZIO), math.radians(ANG_FINE)
ts = np.linspace(t0, t1, SEG)
esterno = [ellisse_pt(t) + ellisse_norm(t) * SPESS / 2 for t in ts]
interno = [ellisse_pt(t) - ellisse_norm(t) * SPESS / 2 for t in ts[::-1]]
arco = cs(esterno + interno)

# punte arrotondate + occhielli
for t, verso in ((t0, -1), (t1, 1)):
    p = ellisse_pt(t)
    tang = np.array([-A_ELLISSE * math.sin(t), B_ELLISSE * math.cos(t)]) * verso
    tang /= np.linalg.norm(tang)
    c = p + tang * (OCCHIELLO_D / 2 - 1.0)
    arco = arco + CrossSection.circle(SPESS / 2, SEG).translate(p.tolist())
    anello = CrossSection.circle(OCCHIELLO_D / 2, SEG).translate(c.tolist())
    foro = CrossSection.circle(FORO_D / 2, SEG).translate(c.tolist())
    arco = (arco + anello) - foro

cerchietto = arco.extrude(ALTEZZA)

# linguette di innesto (lungo l'asse del coltello, a filo col retro z=0)
for phi in (theta, theta + math.pi):
    r = raggio_ellisse(phi)
    rect = rettangolo(r, r + SPESS / 2 + LING_LUNG, -LING_LARG / 2, LING_LARG / 2)
    ling = arrotonda(cs(ruota(rect, phi)), 1.0)
    cerchietto = cerchietto + ling.extrude(LING_H)

# ---------------------------------------------------------------- COLTELLO (sistema dell'asse)
# x lungo l'asse del coltello (punta a x<0, manico a x>0), origine al centro del cerchietto.
r_dx = raggio_ellisse(theta) + SPESS / 2
r_sx = raggio_ellisse(theta + math.pi) + SPESS / 2
h = H_LAMA / 2

# lama: dorso quasi dritto, filo che risale curvo fino alla punta
x_punta = -(r_sx + LAMA_FUORI)
x_curva = x_punta + LAMA_FUORI * 0.55
lama_pts = [(-10.0, h), (x_punta, h - 4.0)]
for k in range(1, 40):  # curva del filo: dalla punta verso il tallone
    u = k / 40
    x = x_punta + (x_curva - x_punta) * u
    y = (h - 4.0) - (H_LAMA - 4.0) * (1 - (1 - u) ** 2.2)
    lama_pts.append((x, y))
lama_pts += [(x_curva, -h), (-10.0, -h)]
sil_lama = arrotonda(cs(lama_pts), 1.2)

# lato manico: tallone della lama + manico con pomolo
x_bolster = r_dx + MOZZO_FUORI
x_fine = x_bolster + L_MANICO
yb, yt = -H_MANICO / 2 + 1.5, H_MANICO / 2 + 1.5  # manico leggermente rialzato rispetto alla lama
mozzo = cs(rettangolo(10.0, x_bolster + 2.0, -h, h))
manico_pts = [
    (x_bolster, yb), (x_fine - 12, yb), (x_fine - 5, yb - 3.5), (x_fine, yb - 1.0),
    (x_fine + 1, yb + 4), (x_fine + 1, yt - 3), (x_fine - 3, yt), (x_bolster, yt),
]
sil_manico = arrotonda(cs(manico_pts), 2.0)
sil_mozzo = arrotonda(mozzo + sil_manico, 1.0)

# impronta del cerchietto in coordinate coltello (pieno + gioco) da sottrarre
ell_pieno = cs([ruota([ellisse_pt(t)], -theta)[0] for t in np.linspace(0, 2 * math.pi, SEG, endpoint=False)])
impronta = ell_pieno.offset(SPESS / 2 + GIOCO_BORDO, JoinType.Round, 2, SEG)


def tasca(phi_rel):
    r = raggio_ellisse(theta + phi_rel)
    rect = rettangolo(r, r + SPESS / 2 + LING_LUNG, -LING_LARG / 2, LING_LARG / 2)
    sez = arrotonda(cs(ruota(rect, phi_rel)), 1.0).offset(GIOCO, JoinType.Round, 2, SEG)
    return sez.extrude(LING_H + GIOCO + 1.0).translate([0, 0, -1.0])


# pezzo LAMA
lama2d = sil_lama - impronta
lama = lama2d.extrude(SP_LAMA) - tasca(math.pi)

# pezzo MANICO: tallone (spessore lama) + manico (piu' spesso) + rivetti incassati
mozzo2d = sil_mozzo - impronta
manico3d = mozzo2d.extrude(SP_LAMA) + sil_manico.extrude(SP_MANICO)
for fx in (0.18, 0.5, 0.82):
    cx = x_bolster + L_MANICO * fx
    manico3d = manico3d - Manifold.cylinder(2.0, 2.6, 2.6, 64).translate([cx, (yb + yt) / 2, SP_MANICO - 0.8])
manico3d = manico3d - tasca(0.0)


# ---------------------------------------------------------------- ESPORTAZIONE
def in_piano(man):
    """Porta il pezzo con il fondo a z=0 e l'ingombro a partire dall'origine."""
    (x0, y0, z0, *_r) = man.bounding_box()
    return man.translate([-x0, -y0, -z0])


def gira(man, ang):
    return man.rotate([0, 0, math.degrees(ang)])


lama_mondo = gira(lama, theta)
manico_mondo = gira(manico3d, theta)

# lama e manico sul piatto con l'asse lungo X
pezzi = {
    "cerchietto.stl": in_piano(cerchietto),
    "lama.stl": in_piano(lama),
    "manico.stl": in_piano(manico3d),
}

if __name__ == "__main__":
    for nome, man in pezzi.items():
        assert man.status() == Error.NoError, nome
        tm = esporta(man, nome)
        ext = tm.bounding_box.extents
        print(f"{nome:16s} {ext[0]:6.1f} x {ext[1]:6.1f} x {ext[2]:4.1f} mm   "
              f"volume {tm.volume / 1000:5.1f} cm3  (~{tm.volume / 1000 * 1.27:4.1f} g pieno)")

    assemblato = cerchietto + lama_mondo + manico_mondo
    esporta(assemblato, "assemblato_anteprima.stl")

    # controlli: niente compenetrazioni tra pezzi, linguette dentro le tasche
    for nome, k in (("lama", lama_mondo), ("manico", manico_mondo)):
        inter = (cerchietto ^ k).volume()
        print(f"compenetrazione cerchietto/{nome}: {inter:.3f} mm3")
        assert inter < 1e-3
