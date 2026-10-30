# Scatola + coperchio per porta-fiala (case-ampoules_rigido).
# Scatola: stesso ingombro dell'originale (80x60x45), pareti/fondo più spessi, due fori Ø8 sul lato corto
# come nell'originale, due torrette per viti al centro dei lati corti.
# Coperchio: piastra piena (solo i 2 fori viti) con culla che tiene il porta-fiala orizzontale,
# centrato, apertura verso l'alto, asse perpendicolare al lato lungo.
import trimesh, numpy as np
from shapely.geometry import box as sbox, Point
from trimesh.creation import extrude_polygon, cylinder

X0, X1, Y0, Y1 = -25.0, 55.0, -35.0, 25.0   # ingombro originale
H      = 45.0
R_ANG  = 5.0       # raggio spigoli verticali
PARETE = 2.5       # era 1.2
FONDO  = 2.5       # era 1.2
CX, CY = (X0+X1)/2, (Y0+Y1)/2

# viti scatola-coperchio (M3 autofilettanti nella plastica)
D_PASS   = 3.4     # foro passante nel coperchio
D_GUIDA  = 2.5     # foro guida nella torretta
R_TORR   = 4.0
H_TORR   = 14.0
P_GUIDA  = 12.0
VITI = [(X0+PARETE+1.5, CY), (X1-PARETE-1.5, CY)]   # al centro dei lati corti

# coperchio + culla
SP_COP  = 3.0
R_CASE  = 19.5     # raggio esterno porta-fiala
GIOCO   = 0.25
SP_CULLA = 3.0
SEC = 160

def rrect(x0, x1, y0, y1, r):
    return sbox(x0+r, y0+r, x1-r, y1-r).buffer(r, resolution=32)
def prism(poly, z0, z1):
    m = extrude_polygon(poly, z1-z0); m.apply_translation([0, 0, z0]); return m
def cyl(r, x, y, z0, z1, sec=64):
    c = cylinder(radius=r, height=z1-z0, sections=sec); c.apply_translation([x, y, (z0+z1)/2]); return c
def cone(r0, r1, x, y, z0, z1, sec=64):
    a = np.linspace(0, 2*np.pi, sec, endpoint=False)
    return trimesh.convex.convex_hull(np.vstack([
        np.c_[x+r0*np.cos(a), y+r0*np.sin(a), np.full(sec, z0)],
        np.c_[x+r1*np.cos(a), y+r1*np.sin(a), np.full(sec, z1)]]))

# ---------------- scatola ----------------
outer = prism(rrect(X0, X1, Y0, Y1, R_ANG), 0, H)
inner = prism(rrect(X0+PARETE, X1-PARETE, Y0+PARETE, Y1-PARETE, R_ANG-PARETE), FONDO, H+1)
box = outer.difference(inner)
torri = []
for (x, y) in VITI:
    t = trimesh.boolean.union([cyl(R_TORR, x, y, H-H_TORR, H),
                               cone(0.3, R_TORR, x, y, H-H_TORR-R_TORR, H-H_TORR)])   # 45°: niente supporti
    torri.append(t.intersection(outer))
box = trimesh.boolean.union([box] + torri)
# i due fori Ø8 dell'originale sul lato corto (x = X1)
fori = []
for y in (-13.44, 3.22):
    f = cylinder(radius=4.0, height=PARETE*3, sections=64)
    f.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    f.apply_translation([X1-PARETE/2, y, 30.0]); fori.append(f)
box = box.difference(trimesh.boolean.union(
    fori + [cyl(D_GUIDA/2, x, y, H-P_GUIDA, H+1) for (x, y) in VITI]))
print('scatola', box.is_watertight, box.bounds.round(2).tolist(), round(box.volume, 1))
box.export(__file__.replace('scatola.py', 'scatola.stl'))

# ---------------- coperchio ----------------
lid = prism(rrect(X0, X1, Y0, Y1, R_ANG), 0, SP_COP)
rc = R_CASE + GIOCO
z_asse = SP_COP + SP_CULLA + rc
culla = prism(sbox(CX-rc-SP_CULLA, Y0, CX+rc+SP_CULLA, Y1), SP_COP-0.01, z_asse)
tubo = cylinder(radius=rc, height=(Y1-Y0)+2, sections=SEC)
tubo.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0]))
tubo.apply_translation([CX, CY, z_asse])
lid = trimesh.boolean.union([lid, culla.difference(tubo)])
lid = lid.difference(trimesh.boolean.union([cyl(D_PASS/2, x, y, -1, SP_COP+1) for (x, y) in VITI]))
print('coperchio', lid.is_watertight, lid.bounds.round(2).tolist(), round(lid.volume, 1))
lid.export(__file__.replace('scatola.py', 'coperchio.stl'))
