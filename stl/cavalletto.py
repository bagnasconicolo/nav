# Cavalletto: tiene scatola + coperchio + porta-fiala con il tubo verticale (coppa in basso),
# scatola appoggiata sulla faccia grande (lato lungo) dentro una vaschetta, tutto inclinato
# all'indietro di INCLINAZIONE gradi. La parte bassa del tubo (che sporge oltre la scatola)
# entra in una sede a mezzo tubo che lo sostiene da dietro.
import trimesh, numpy as np
from trimesh.creation import box as tbox, cylinder

INCLINAZIONE = 10.0   # gradi, la cima va verso la scatola (indietro)
GIOCO   = 0.4         # gioco vaschetta / sede tubo
BORDO   = 3.0         # spessore bordo vaschetta
H_BORDO = 8.0         # altezza bordo vaschetta
BASE    = 5.0         # spessore piastra a terra
FONDO_SEDE = 3.0      # materiale sotto la coppa del tubo
MARGINE = 15.0        # quanto la piastra sporge oltre il cavalletto
MARGINE_FRONTE = 30.0 # in più davanti (lato apertura del tubo)

# --- assieme in coordinate "A" (come nel render): scatola x[-25,55] y[-35,25] z[-45,0],
# coperchio sopra (z>0), tubo con asse lungo y in x=15, z=Z_ASSE, da y=-80 a y=70, apertura verso +z
Z_ASSE = 3 + 3 + 19.75 - 0.25
R_TUBO = 19.5
Y_FACCIA, Y_FONDO_TUBO = -35.0, -80.0

def bx(x0, x1, y0, y1, z0, z1):
    b = tbox(extents=[x1-x0, y1-y0, z1-z0]); b.apply_translation([(x0+x1)/2, (y0+y1)/2, (z0+z1)/2]); return b

g, t = GIOCO, BORDO
ped = bx(-25-g-t, 55+g+t, -400, Y_FACCIA, -45-g-t, Z_ASSE)
rim = bx(-25-g-t, 55+g+t, Y_FACCIA-1, Y_FACCIA+H_BORDO, -45-g-t, 0).difference(
      bx(-25-g, 55+g, Y_FACCIA-2, Y_FACCIA+H_BORDO+1, -45-g, 1))
sede = cylinder(radius=R_TUBO+g, height=400, sections=160)
sede.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2, [1, 0, 0]))   # asse z -> y
sede.apply_translation([15, Y_FONDO_TUBO-g+200, Z_ASSE])
stand = trimesh.boolean.union([ped, rim]).difference(sede)

# --- da A a mondo: y_A diventa verticale, inclinato indietro (verso -z_A)
th = np.radians(INCLINAZIONE)
n = np.array([0, np.cos(th), np.sin(th)])                       # verticale del mondo, in coordinate A
T = np.eye(4); T[:3, :3] = np.array([[1, 0, 0], np.cross(n, [1, 0, 0]), n])
# punto più basso del fondo del tubo -> appoggia a BASE + FONDO_SEDE da terra
a = np.linspace(0, 2*np.pi, 90)
fondo = np.c_[15+R_TUBO*np.cos(a), np.full(90, Y_FONDO_TUBO), Z_ASSE+R_TUBO*np.sin(a)]
T[2, 3] = BASE + FONDO_SEDE - (fondo @ n).min()
stand.apply_transform(T)
stand = stand.intersection(bx(-500, 500, -500, 500, 0, 500))
# piastra a terra
lo, hi = stand.bounds
fr = np.cross(n, [1, 0, 0]) @ np.array([0, 0, 1])               # direzione "davanti" (+z_A) nel mondo, componente y
y0, y1 = lo[1]-MARGINE, hi[1]+MARGINE
if fr > 0: y1 += MARGINE_FRONTE
else:      y0 -= MARGINE_FRONTE
piastra = trimesh.creation.extrude_polygon(
    __import__('shapely').geometry.box(lo[0]-MARGINE, y0, hi[0]+MARGINE, y1).buffer(-6).buffer(6), BASE)
stand = trimesh.boolean.union([stand, piastra])
print('cavalletto', stand.is_watertight, stand.bounds.round(1).tolist(), round(stand.volume/1000, 1), 'cm3')
stand.export(__file__.replace('.py', '.stl'))
np.save(__file__.replace('.py', '_T.npy'), T)   # trasformazione A -> mondo (per il render)
