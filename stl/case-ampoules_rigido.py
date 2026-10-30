# Porta-fiala rigido: coppa inferiore + dorso a mezzo cilindro + collare superiore, pezzo unico.
import trimesh, numpy as np
from trimesh.creation import cylinder, box
CX, CY = -60.0, 0.0       # asse fiala (come originale)
R_IN  = 15.5              # raggio interno (fiala Ø31, come originale)
R_OUT = 19.5              # dorso spesso 4 mm -> rigido
H     = 150.0
FLOOR = 1.2
CUP_H = 15.0              # coppa inferiore (gommapiuma + elettrodo)
TOP_H = 15.0              # collare superiore (elettrodo circolare)
GW, GD = 3.0, 2.0         # scanalatura cavo sul dorso (larghezza, profondità)
SEC = 160

def cyl(r, z0, z1):
    c = cylinder(radius=r, height=z1-z0, sections=SEC)
    c.apply_translation([CX, CY, (z0+z1)/2]); return c
def bx(x0, x1, y0, y1, z0, z1):
    b = box(extents=[x1-x0, y1-y0, z1-z0]); b.apply_translation([(x0+x1)/2, (y0+y1)/2, (z0+z1)/2]); return b
def frustum(r0, r1, z0, z1):
    a = np.linspace(0, 2*np.pi, SEC, endpoint=False)
    p0 = np.c_[CX+r0*np.cos(a), CY+r0*np.sin(a), np.full(SEC, z0)]
    p1 = np.c_[CX+r1*np.cos(a), CY+r1*np.sin(a), np.full(SEC, z1)]
    return trimesh.convex.convex_hull(np.vstack([p0, p1]))

# mezzo cilindro posteriore, a tutta altezza
shell = cyl(R_OUT, 0, H).difference(cyl(R_IN, FLOOR, H+1))
back  = shell.intersection(bx(CX-R_OUT-1, CX, -R_OUT-1, R_OUT+1, -1, H+1))
# coppa inferiore e collare superiore: anelli completi
ring_lo = cyl(R_OUT, 0, CUP_H).difference(cyl(R_IN, FLOOR, CUP_H+1))
ring_hi = cyl(R_OUT, H-TOP_H, H).difference(cyl(R_IN, 0, H+1))
# raccordo a 45° sotto il collare: si stampa in piedi senza supporti
d = R_OUT - R_IN
cone_hi = frustum(R_IN, R_OUT, H-TOP_H-d, H-TOP_H).difference(cyl(R_IN, 0, H+1))
body = trimesh.boolean.union([back, ring_lo, ring_hi, cone_hi])
# invito 1x45° all'imbocco in alto
body = body.difference(frustum(R_IN, R_IN+1.0, H-1.0, H+0.01))
# scanalatura cavo sul dorso + passaggi nella coppa e nel collare
xg = CX - R_OUT
groove  = bx(xg-1, xg+GD, -GW/2, GW/2, -1, H+1)
hole_lo = bx(xg-1, CX-R_IN+1, -GW/2, GW/2, FLOOR, FLOOR+3.2)
hole_hi = bx(xg-1, CX-R_IN+1, -GW/2, GW/2, H-TOP_H+2, H+1)
body = body.difference(trimesh.boolean.union([groove, hole_lo, hole_hi]))
print(body.is_watertight, body.bounds.round(2).tolist(), round(body.volume, 1))
body.export(__file__.replace('.py', '.stl'))
