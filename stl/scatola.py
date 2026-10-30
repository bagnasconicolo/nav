# Scatola + coperchio per porta-fiala (case-ampoules_rigido).
# Scatola: stesso ingombro dell'originale (80x60x45), pareti/fondo più spessi, passacavi in alto sul lato corto, due torrette per viti al centro dei lati corti.
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
# passacavi in alto sul lato corto, ai lati della torretta centrale
D_CAVO, H_CAVO = 6.0, 9.0
PASSACAVI_Y = (CY-14.0, CY+14.0)
VITI = [(X0+PARETE+1.5, CY), (X1-PARETE-1.5, CY)]   # al centro dei lati corti

# coperchio + culla
SP_COP  = 3.0
R_CASE  = 19.5     # raggio esterno porta-fiala
GIOCO   = 0.25
SP_CULLA = 3.0     # spessore sotto il tubo
LAT_CULLA = 2.5    # spessore pareti laterali all'altezza dell'asse (devono flettere per lo scatto)
# scatto: sopra l'asse le pareti hanno un dentino che si chiude sui bordi del mezzo cilindro
SCATTO   = 0.6     # interferenza per lato (0.4 = più morbido, 0.8 = più duro)
H_DENTE  = 1.5     # tratto dritto del dentino sopra l'asse
H_INVITO = 2.0     # smusso d'ingresso sopra il dentino
# bordo del coperchio: battuta che entra nella scatola
H_BORDO  = 3.0
GIOCO_BORDO = 0.3  # per lato
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
# passacavi: tacche a U sul lato corto (x = X1), aperte in alto; col coperchio chiuso diventano fori
fori = []
for y in PASSACAVI_Y:
    f = cylinder(radius=D_CAVO/2, height=PARETE*3, sections=64)
    f.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    f.apply_translation([X1-PARETE/2, y, H-H_CAVO+D_CAVO/2])
    t = trimesh.creation.box(extents=[PARETE*3, D_CAVO, H_CAVO])
    t.apply_translation([X1-PARETE/2, y, H-H_CAVO/2+D_CAVO/2+0.5])
    fori.append(trimesh.boolean.union([f, t]))
box = box.difference(trimesh.boolean.union(
    fori + [cyl(D_GUIDA/2, x, y, H-P_GUIDA, H+1) for (x, y) in VITI]))
print('scatola', box.is_watertight, box.bounds.round(2).tolist(), round(box.volume, 1))
box.export(__file__.replace('scatola.py', 'scatola.stl'))

# ---------------- coperchio ----------------
# battuta (z 0..H_BORDO) che entra nella scatola, piastra sopra (H_BORDO..H_BORDO+SP_COP)
g = PARETE + GIOCO_BORDO
bordo = prism(rrect(X0+g, X1-g, Y0+g, Y1-g, R_ANG-PARETE), 0, H_BORDO+0.01)
bordo = bordo.difference(trimesh.boolean.union(
    [cyl(R_TORR+GIOCO_BORDO, x, y, -1, H_BORDO+1) for (x, y) in VITI]))      # incavi per le torrette
z_pia = H_BORDO + SP_COP
lid = trimesh.boolean.union([bordo, prism(rrect(X0, X1, Y0, Y1, R_ANG), H_BORDO, z_pia)])
# culla a scatto: profilo nel piano xz, estruso lungo y
rc = R_CASE + GIOCO
z_asse = z_pia + SP_CULLA + rc
w = rc + LAT_CULLA
wd = R_CASE - SCATTO                     # semiapertura del dentino
z_top = z_asse + H_DENTE + H_INVITO
from shapely.geometry import Polygon
a = np.linspace(np.pi, 2*np.pi, 90)
prof = Polygon([(CX-w, z_pia-0.01), (CX+w, z_pia-0.01), (CX+w, z_top), (CX+wd+H_INVITO, z_top),
                (CX+wd, z_asse+H_DENTE), (CX+wd, z_asse), (CX+rc, z_asse)]
               + [(CX+rc*np.cos(t), z_asse+rc*np.sin(t)) for t in a[::-1]][1:-1]
               + [(CX-rc, z_asse), (CX-wd, z_asse), (CX-wd, z_asse+H_DENTE), (CX-wd-H_INVITO, z_top), (CX-w, z_top)])
culla = extrude_polygon(prof, Y1-Y0)                 # profilo in xy, estrusione lungo z ...
culla.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0]))   # ... y->z, z->-y
culla.apply_translation([0, Y1, 0])
lid = trimesh.boolean.union([lid, culla])
lid = lid.difference(trimesh.boolean.union([cyl(D_PASS/2, x, y, -1, z_pia+1) for (x, y) in VITI]))
print('coperchio', lid.is_watertight, lid.bounds.round(2).tolist(), round(lid.volume, 1))
lid.export(__file__.replace('scatola.py', 'coperchio.stl'))
