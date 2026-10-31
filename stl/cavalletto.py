# Cavalletto "monolite": un unico blocco morbido (pianta: rettangolo dietro, semicerchio davanti) su cui la scatola si incassa appoggiata sulla
# faccia grande e il porta-fiala si pianta verticale, il tutto inclinato all'indietro.
# Modellato come campo di distanza (SDF) con raccordi morbidi, poi convertito in mesh.
import numpy as np, trimesh
from skimage.measure import marching_cubes

INCLINAZIONE = 10.0   # gradi, la cima va verso la scatola (indietro)
GIOCO   = 0.4         # gioco nelle sedi
INCASSO = 10.0        # quanto la scatola affonda nel blocco
PARETE  = 6.0         # spessore minimo del blocco attorno alle sedi
FONDO_SEDE = 4.0      # materiale sotto la coppa del tubo
R_ESTERNO = 10.0      # raccordo degli spigoli esterni
R_BORDI   = 1.5       # raccordo dei bordi delle sedi
R_FINESTRA = 8.0      # raccordo della finestra davanti al tubo
OMBRA   = 2.0         # linea d'ombra alla base (altezza = rientro)
RES     = 0.4         # risoluzione mesh (mm)

# assieme in coordinate "A": scatola x[-25,55] y[-35,25] z[-45,0], coperchio sopra (z>0),
# tubo con asse lungo y in x=15, z=Z_ASSE, da y=-80 a y=70, apertura verso +z
Z_ASSE = 3 + 3 + 19.75 - 0.25
R_TUBO = 19.5
Y_FACCIA, Y_FONDO_TUBO, H_COPPA = -35.0, -80.0, 15.0
XC = 15.0

# --- A -> mondo: y_A diventa la verticale, inclinata indietro (verso -z_A)
th = np.radians(INCLINAZIONE)
n = np.array([0, np.cos(th), np.sin(th)])
R = np.array([[1, 0, 0], np.cross(n, [1, 0, 0]), n])
a = np.linspace(0, 2*np.pi, 90)
fondo = np.c_[XC+R_TUBO*np.cos(a), np.full(90, Y_FONDO_TUBO), Z_ASSE+R_TUBO*np.sin(a)]
tz = FONDO_SEDE - (fondo @ n).min()
T = np.eye(4); T[:3, :3] = R; T[2, 3] = tz

# --- primitive SDF (negativo = dentro)
def sbox(p, lo, hi):
    c = (np.array(lo)+hi)/2; h = (np.array(hi)-lo)/2
    q = np.abs(p-c) - h
    return np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(q.max(-1), 0)
def smin(a, b, k):
    h = np.clip(0.5 + 0.5*(b-a)/k, 0, 1); return b*(1-h) + a*h - k*h*(1-h)
def smax(a, b, k): return -smin(-a, -b, k)

g = GIOCO
BIG = 1e3
def campo(pw):
    p = (pw - [0, 0, tz]) @ R            # mondo -> A (R ortogonale)
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    # pianta "a lapide": rettangolo dietro (spigoli R_ESTERNO) + semicerchio pieno davanti,
    # estrusa lungo la verticale del tubo, bordo superiore raggiato R_ESTERNO
    y_top = Y_FACCIA + INCASSO
    rr = R_ESTERNO
    hx = 40 + g + PARETE                          # semilarghezza (scatola 80 mm)
    z_dietro = -45 - g - PARETE
    zc = Z_ASSE + R_TUBO + g + PARETE - hx        # centro del semicerchio frontale
    rett = sbox(np.stack([x, z], -1), [XC-hx+rr, z_dietro+rr], [XC+hx-rr, zc]) - rr
    semi = np.where(z > zc, np.hypot(x-XC, z-zc) - hx, BIG)
    pianta = np.minimum(rett, semi)
    q0 = pianta + rr; q1 = y - (y_top - rr)
    corpo = np.hypot(np.maximum(q0, 0), np.maximum(q1, 0)) + np.minimum(np.maximum(q0, q1), 0) - rr
    r = np.hypot(x-XC, z-Z_ASSE)
    # sedi: scatola + piastra coperchio, culla a scatto, tubo
    vano = np.minimum(sbox(p, [-25-g, Y_FACCIA, -45-g], [55+g, BIG, 3+g]),
                      sbox(p, [XC-22.25-g, Y_FACCIA, 0], [XC+22.25+g, BIG, Z_ASSE+4.5]))
    tubo = np.maximum(r-(R_TUBO+g), Y_FONDO_TUBO-g-y)
    d = smax(corpo, -np.minimum(vano, tubo), R_BORDI)
    # finestra davanti al tubo, sopra la coppa: la fiala resta visibile
    fin = sbox(p, [XC-(R_TUBO+g)+1.0, Y_FONDO_TUBO+H_COPPA, Z_ASSE], [XC+(R_TUBO+g)-1.0, BIG, BIG])
    d = smax(d, -fin, R_FINESTRA)
    # linea d'ombra: zoccolo rientrato di OMBRA alla base, il blocco sembra sospeso
    d = np.where(pw[..., 2] < OMBRA, np.maximum(d, corpo+OMBRA), d)
    return np.maximum(d, -pw[..., 2])

# --- griglia sui limiti dell'oggetto
cor = np.array([[x, y, z] for x in (-25-g-PARETE, 55+g+PARETE) for y in (Y_FONDO_TUBO-10, Y_FACCIA+INCASSO)
                for z in (-45-g-PARETE, Z_ASSE+R_TUBO+g+PARETE)])
w = cor @ R.T + [0, 0, tz]
lo = w.min(0) - 3; hi = w.max(0) + 3; lo[2] = -1
ax = [np.arange(lo[i], hi[i], RES) for i in range(3)]
G = np.stack(np.meshgrid(*ax, indexing='ij'), -1).astype(np.float32)
D = np.empty(G.shape[:3], np.float32)
for i in range(G.shape[0]):
    D[i] = campo(G[i].astype(np.float64))
v, f, _, _ = marching_cubes(D, 0.0, spacing=(RES, RES, RES))
m = trimesh.Trimesh(v + lo, f[:, ::-1], process=True)
m.update_faces(m.nondegenerate_faces()); m.merge_vertices(); m.fix_normals()
v = m.vertices; v[np.abs(v[:, 2]) < RES*0.75, 2] = 0.0; m.vertices = v   # base perfettamente piana
m = m.simplify_quadric_decimation(face_count=120000) if len(m.faces) > 120000 else m
print('cavalletto', m.is_watertight, m.bounds.round(1).tolist(), round(m.volume/1000, 1), 'cm3', len(m.faces))
m.export(__file__.replace('.py', '.stl'))
np.save(__file__.replace('.py', '_T.npy'), T)
