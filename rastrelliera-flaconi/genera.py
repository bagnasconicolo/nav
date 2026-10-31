"""COROLLA — portaflaconi per 5 flaconi Ø40 x 70 mm. Creality K2, PETG-CF.

Cinque flaconi disposti in cerchio, ciascuno inclinato verso l'esterno come i petali di un
fiore che si apre. Il corpo è un pentalobo morbido che segue i flaconi, con un vuoto al centro.
Bordi raccordati, linea d'ombra alla base: sembra appoggiato appena sopra il piano.

pip install manifold3d trimesh numpy  ->  python3 genera.py
"""
import math
import numpy as np
from manifold3d import Manifold, CrossSection, JoinType

# ---------------- parametri (mm) ----------------
N         = 5
D_FORO    = 42.0          # flacone Ø40 + 1 mm di gioco per lato
PARETE    = 4.0           # parete minima attorno a ogni flacone (in basso)
PASSO     = D_FORO + 3.5  # distanza tra flaconi vicini
INCLINA   = 7.0           # gradi di apertura verso l'esterno
H         = 22.0          # altezza
FONDO     = 1.6           # spessore minimo del fondo (nel punto più basso della tasca)
R_BORDO   = 2.0           # raccordo dei bordi superiori (esterno e foro centrale)
R_INVITO  = 1.0           # raccordo d'imbocco delle tasche
OMBRA     = 1.2           # smusso rientrante alla base
R_VITA    = 14.0          # raggio dei raccordi concavi tra un lobo e l'altro
D_CENTRO  = 22.0          # vuoto centrale
SEG       = 128

RC = PASSO / (2 * math.sin(math.pi / N))      # raggio del cerchio dei flaconi
_T = math.radians(INCLINA)
_Z0 = FONDO + (D_FORO / 2) * math.sin(_T)
# lobo dimensionato sul punto critico: bordo esterno in alto, dove la tasca inclinata si avvicina
R_LOBO = max(D_FORO / 2 + PARETE,
             (H - _Z0) * math.tan(_T) + (D_FORO / 2) / math.cos(_T) + R_INVITO + 1.5 + R_BORDO)


def pianta():
    """Pentalobo: cerchi attorno ai flaconi, vita raccordata, vuoto centrale."""
    lobi = CrossSection()
    for i in range(N):
        a = 2 * math.pi * i / N + math.pi / 2
        lobi += CrossSection.circle(R_LOBO, SEG).translate((RC * math.cos(a), RC * math.sin(a)))
    lobi = lobi.offset(R_VITA, JoinType.Round, circular_segments=SEG).offset(
        -R_VITA, JoinType.Round, circular_segments=SEG)            # chiusura = vita morbida
    return (lobi - CrossSection.circle(D_CENTRO / 2, SEG)).simplify(0.02)


DZ, Q = 0.05, 0.1


def gradini(za, zb, R, dz=None, q=None):
    """Divide un raccordo a quarto di cerchio (da za a zb, raggio R) in gradini orizzontali.
    Il rientro è quantizzato a passi di q mm: i gradini quasi uguali vengono fusi,
    così non si formano pareti quasi coincidenti (mesh pulita)."""
    dz, q = dz or DZ, q or Q
    out = []
    z = za
    while z < zb - 1e-9:
        h = z + dz / 2 - za
        ins = round((R - math.sqrt(max(R * R - h * h, 0))) / q) * q
        if out and abs(out[-1][2] - ins) < 1e-9:
            out[-1][1] = min(z + dz, zb)
        else:
            out.append([z, min(z + dz, zb), ins])
        z += dz
    return [tuple(o) for o in out]


def corpo():
    """Estrusione a gradini sottili (0,1 mm) per raccordare tutti i bordi, anche quelli concavi."""
    base = pianta()
    dz = 0.1
    m = Manifold.extrude(base, H - R_BORDO - OMBRA).translate((0, 0, OMBRA))
    z = 0.0
    while z < OMBRA - 1e-6:                                         # linea d'ombra 45°
        m += Manifold.extrude(base.offset(-(OMBRA - z - dz / 2)), dz).translate((0, 0, z))
        z += dz
    for z0, z1, ins in gradini(H - R_BORDO, H, R_BORDO):           # raccordo superiore
        m += Manifold.extrude(base.offset(-ins, JoinType.Round, circular_segments=SEG), z1 - z0).translate((0, 0, z0))
    return m


def tasca():
    """Cilindro del flacone, asse lungo z, fondo piatto a z=0."""
    return Manifold.cylinder(60, D_FORO / 2, D_FORO / 2, SEG)


def corolla():
    m = corpo()
    t = math.radians(INCLINA)
    # il punto più basso del fondo inclinato deve stare a FONDO: alzo la tasca di conseguenza
    z0 = FONDO + (D_FORO / 2) * math.sin(t)
    for i in range(N):
        a = 360 * i / N + 90
        p = tasca().rotate((0, INCLINA, 0)).translate((RC, 0, z0)).rotate((0, 0, a))
        m -= p
        # imbocco raccordato nel piano orizzontale: sezioni ellittiche del cilindro inclinato
        for za, zb, ins in gradini(H - R_INVITO, H, R_INVITO):
            r = D_FORO / 2 + ins
            zb = zb + 0.5 if zb >= H - 1e-9 else zb
            x = RC + ((za + zb) / 2 - z0) * math.tan(t)
            ell = CrossSection.circle(r, SEG).scale((1 / math.cos(t), 1)).translate((x, 0))
            m -= Manifold.extrude(ell, zb - za).translate((0, 0, za)).rotate((0, 0, a))
    return m


if __name__ == "__main__":
    import trimesh, io
    # la discretizzazione dei raccordi a gradini può lasciare qualche spigolo doppio quando
    # l'STL arrotonda a float32: provo alcuni passi e tengo il primo che dà una mesh chiusa
    for DZ, Q in [(0.05, 0.1), (0.1, 0.1), (0.05, 0.2), (0.1, 0.2)]:
        mesh = corolla().simplify(0.005).to_mesh()
        tm = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts))
        buf = io.BytesIO(); tm.export(buf, file_type="stl"); buf.seek(0)
        if trimesh.load(buf, file_type="stl").is_watertight:
            break
    tm.export("corolla_5.stl")
    tm = trimesh.load("corolla_5.stl")
    b = tm.bounds
    print(f"corolla_5.stl: {np.round(b[1]-b[0],1)} mm, volume {tm.volume/1000:.1f} cm³, "
          f"watertight={tm.is_watertight} (passo {DZ}/{Q}), R_LOBO={R_LOBO:.1f}")
