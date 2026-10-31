"""Rastrelliera per 5 flaconi Ø40 x 70 mm — Creality K2, PETG-CF.

Una forma sola: una capsula bassa e continua, raccordi morbidi, nessun dettaglio superfluo.
Sotto, uno smusso rientrante crea una linea d'ombra: il pezzo sembra sospeso sul piano.

Genera l'STL con manifold3d:  pip install manifold3d trimesh numpy
"""
import math
import numpy as np
from manifold3d import Manifold, CrossSection

# ---------------- parametri (mm) ----------------
N         = 5
D_FLACONE = 40.0
GIOCO     = 1.0                      # gioco radiale -> foro Ø42
D_FORO    = D_FLACONE + 2 * GIOCO
PARETE    = 3.5                      # parete esterna e tra i fori
PASSO     = D_FORO + PARETE          # 45,5
H         = 20.0                     # altezza totale
FONDO     = 1.6                      # fondo pieno (8 layer da 0,2)
R_BORDO   = 2.0                      # raccordo del bordo superiore esterno
R_INVITO  = 1.2                      # raccordo d'invito sul bordo dei fori
OMBRA     = 1.2                      # smusso rientrante alla base (45°, stampabile senza supporti)
SEG       = 160
PASSI_RACCORDO = 12

L = (N - 1) * PASSO + D_FORO + 2 * PARETE   # lunghezza
W = D_FORO + 2 * PARETE                      # larghezza = diametro delle estremità


def capsula(inset):
    """Profilo a capsula (stadio) ridotto di 'inset'."""
    r = W / 2 - inset
    rett = CrossSection.square((L - W, 2 * r), center=True)
    ext = CrossSection.circle(r, SEG)
    return rett + ext.translate((-(L - W) / 2, 0)) + ext.translate(((L - W) / 2, 0))


def fetta(inset, z):
    return Manifold.extrude(capsula(inset), 0.001).translate((0, 0, z))


def corpo():
    fette = [fetta(OMBRA, 0), fetta(0, OMBRA)]
    for k in range(PASSI_RACCORDO + 1):                     # raccordo superiore a quarto di cerchio
        t = k / PASSI_RACCORDO * math.pi / 2
        fette.append(fetta(R_BORDO * (1 - math.cos(t)), H - R_BORDO + R_BORDO * math.sin(t) - 0.001))
    return Manifold.batch_hull(fette)


def tasca(x):
    """Tasca di rivoluzione: fondo piatto, parete dritta, invito raccordato."""
    r = D_FORO / 2
    prof = [(0, FONDO), (r, FONDO)]
    for k in range(PASSI_RACCORDO + 1):
        t = k / PASSI_RACCORDO * math.pi / 2
        prof.append((r + R_INVITO - R_INVITO * math.cos(t), H - R_INVITO + R_INVITO * math.sin(t)))
    prof += [(r + R_INVITO, H + 1), (0, H + 1)]
    return Manifold.revolve(CrossSection([prof]), SEG).translate((x, 0, 0))


def rastrelliera():
    m = corpo()
    for i in range(N):
        m -= tasca((i - (N - 1) / 2) * PASSO)
    return m


if __name__ == "__main__":
    import trimesh
    mesh = rastrelliera().to_mesh()
    tm = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts))
    tm.export("rastrelliera_5.stl")
    b = tm.bounds
    print(f"rastrelliera_5.stl: {np.round(b[1]-b[0],1)} mm, volume {tm.volume/1000:.1f} cm³, "
          f"watertight={tm.is_watertight}")
