# Cavalletto leggero: tiene scatola + porta-fiala con il tubo verticale, inclinato all'indietro.
# Struttura a lastre sottili con raccordi morbidi:
#  - ripiano su cui appoggia la faccia grande della scatola (con un'apertura che lo alleggerisce)
#  - due fianchi sottili che scendono a terra, alleggeriti da un arco ellittico
#  - anello che accoglie la coppa del tubo e sale fino al ripiano dietro al tubo;
#    davanti si apre con un taglio curvo a 45° che lascia vedere la fiala.
# Modellato come campo di distanza (SDF), convertito in mesh. L'STL è già orientato per la stampa
# (ripiano sul piatto): nessun supporto.
import numpy as np, trimesh
from skimage.measure import marching_cubes

INCLINAZIONE = 10.0   # gradi, la cima va verso la scatola (indietro)
GIOCO   = 0.4
SP      = 3.0         # spessore lastre
R_SAGOMA = 12.0       # raggio degli angoli dei fianchi
R_BORDO  = 1.2        # arrotondamento dei bordi delle lastre
R_GIUNTO = 3.0        # raccordo tra le parti
FINESTRA_RIPIANO = 12.0   # cornice del ripiano attorno all'apertura (0 = ripiano pieno)
H_ANELLO = 10.0       # altezza dell'anello davanti alla coppa
ARCO_PIEDE  = 16.0    # larghezza dei piedi ai lati dell'arco nei fianchi
ARCO_FASCIA = 12.0    # materiale minimo sopra la chiave dell'arco
RES     = 0.35

# assieme in coordinate "A": scatola x[-25,55] y[-35,25] z[-45,0], coperchio sopra (z>0),
# tubo con asse lungo y in x=15, z=Z_ASSE, da y=-80 a y=70, apertura verso +z
Z_ASSE = 3 + 3 + 19.75 - 0.25
R_TUBO = 19.5
Y_FACCIA, Y_FONDO = -35.0, -80.0
XC, X0, X1, ZB = 15.0, -25.0, 55.0, -45.0
Z_CULLA = Z_ASSE + 4.5                  # fin dove arriva la culla del coperchio sul ripiano

g = GIOCO
RI = R_TUBO + g                          # raggio interno anello
RA = RI + SP                             # raggio esterno anello
Y_LEDGE = Y_FONDO - g                    # dove appoggia il bordo della coppa
Y_BASE = Y_LEDGE - 3.0                   # fondo dell'anello (smusso 45° di 3 mm)

# --- A -> mondo: y_A verticale, inclinata indietro (verso -z_A); l'anello tocca terra
th = np.radians(INCLINAZIONE)
n = np.array([0, np.cos(th), np.sin(th)])
R = np.array([[1, 0, 0], np.cross(n, [1, 0, 0]), n])
a = np.linspace(0, 2*np.pi, 180)
anello = np.c_[XC+RA*np.cos(a), np.full(180, Y_BASE), Z_ASSE+RA*np.sin(a)]
tz = -(anello @ n).min()
T = np.eye(4); T[:3, :3] = R; T[2, 3] = tz

# arco ellittico nei fianchi (nel piano verticale del mondo), aperto a terra
def _mondo(yA, zA): return np.array([0, yA, zA]) @ R.T + [0, 0, tz]
_dav = _mondo((-tz - n[2]*(Z_ASSE+RA)) / n[1], Z_ASSE+RA)[1]     # piede davanti a terra (Y mondo)
_die = _mondo((-tz - n[2]*(ZB-g-SP)) / n[1], ZB-g-SP)[1]          # piede dietro a terra (Y mondo)
ARCO_A = (_die - _dav)/2 - ARCO_PIEDE
ARCO_YC = (_die + _dav)/2
_t0, _t1 = _mondo(Y_FACCIA, Z_ASSE+RA), _mondo(Y_FACCIA, ZB-g-SP)  # bordo superiore del fianco
ARCO_B = _t0[2] + (ARCO_YC-_t0[1])*(_t1[2]-_t0[2])/(_t1[1]-_t0[1]) - ARCO_FASCIA

def sbox(p, lo, hi):
    c = (np.array(lo)+hi)/2; h = (np.array(hi)-lo)/2
    q = np.abs(p-c) - h
    return np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(q.max(-1), 0)
def rbox(p, lo, hi, r):                  # box con spigoli arrotondati r
    return sbox(p, np.array(lo)+r, np.array(hi)-r) - r
def smin(a, b, k):
    h = np.clip(0.5 + 0.5*(b-a)/k, 0, 1); return b*(1-h) + a*h - k*h*(1-h)
def smax(a, b, k): return -smin(-a, -b, k)
def lastra(d2, t, r):                    # profilo 2D d2 estruso; t = distanza dalle facce (negativa dentro)
    return np.hypot(np.maximum(d2+r, 0), np.maximum(t+r, 0)) + np.minimum(np.maximum(d2+r, t+r), 0) - r

BIG = 1e3
def campo(pw):
    p = (pw - [0, 0, tz]) @ R
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    zw = pw[..., 2]
    r = np.hypot(x-XC, z-Z_ASSE)
    z_fronte = Z_ASSE + RA
    # ripiano (sotto la faccia della scatola), tra i due fianchi
    rip = rbox(p, [X0-g, Y_FACCIA-SP, ZB-g-SP], [X1+g, Y_FACCIA, Z_CULLA], R_BORDO)
    if FINESTRA_RIPIANO > 0:
        fin = rbox(p, [X0+FINESTRA_RIPIANO, -BIG, ZB+FINESTRA_RIPIANO], [X1-FINESTRA_RIPIANO, BIG, -FINESTRA_RIPIANO], 6.0)
        rip = smax(rip, -fin, 1.5)
    # fianchi: sagoma nel piano (y,z) con angoli raggiati, da terra al ripiano
    sag = rbox(np.stack([y, z], -1), [Y_BASE-60, ZB-g-SP], [Y_FACCIA, z_fronte], R_SAGOMA)
    ell = (np.hypot((pw[..., 1]-ARCO_YC)/ARCO_A, zw/ARCO_B) - 1) * min(ARCO_A, ARCO_B)
    sag = smax(sag, -ell, 3.0)                                   # arco
    sag = np.maximum(sag, -zw)                                   # tagliata a terra
    fx = np.minimum(np.abs(x-(X0-g-SP/2)), np.abs(x-(X1+g+SP/2))) - SP/2
    fianchi = lastra(sag, fx, R_BORDO)
    # anello per la coppa: tutto intorno in basso; dietro sale fino al ripiano;
    # davanti il bordo sale lungo l'arco a 45° fino al ripiano
    phi = np.abs(np.arctan2(x-XC, z-Z_ASSE))                     # 0 = davanti
    y_lim = np.minimum(Y_LEDGE + H_ANELLO + RA*phi, Y_FACCIA)
    guscio = np.abs(r - (RI+RA)/2) - SP/2
    anel = np.maximum(guscio, np.maximum(y - y_lim, Y_BASE - y))
    # smusso interno a 45° su cui appoggia il bordo della coppa
    ledge = np.maximum(np.maximum((RI - 3.0) - r, r - RA + 0.01),
                       np.maximum(y - (Y_LEDGE - (RI - r)), Y_BASE - y))
    anel = np.minimum(anel, ledge)
    corpo = smin(smin(rip, fianchi, R_GIUNTO), anel, R_GIUNTO)
    # i raccordi non devono invadere tubo e scatola
    tubo = np.maximum(r - RI, Y_LEDGE - (RI - r) - y)
    scat = sbox(p, [X0-g, Y_FACCIA, ZB-g], [X1+g, BIG, Z_CULLA])
    d = np.maximum(corpo, -np.minimum(tubo, scat))
    return np.maximum(d, -zw)

cor = np.array([[x, y, z] for x in (X0-g-SP-2, X1+g+SP+2) for y in (Y_BASE-60, Y_FACCIA+2)
                for z in (ZB-g-SP-2, Z_ASSE+RA+2)])
w = cor @ R.T + [0, 0, tz]
lo = w.min(0) - 2; hi = w.max(0) + 2; lo[2] = -1
ax = [np.arange(lo[i], hi[i], RES) for i in range(3)]
D = np.empty((len(ax[0]), len(ax[1]), len(ax[2])), np.float32)
YY, ZZ = np.meshgrid(ax[1], ax[2], indexing='ij')
for i, xv in enumerate(ax[0]):
    D[i] = campo(np.stack([np.full_like(YY, xv), YY, ZZ], -1))
v, f, _, _ = marching_cubes(D, 0.0, spacing=(RES, RES, RES))
m = trimesh.Trimesh(v + lo, f[:, ::-1], process=True)
m.update_faces(m.nondegenerate_faces()); m.merge_vertices(); m.fix_normals()
m = m.simplify_quadric_decimation(face_count=150000) if len(m.faces) > 150000 else m
m.fix_normals()
print('cavalletto', m.is_watertight, m.bounds.round(1).tolist(), round(m.volume/1000, 1), 'cm3', len(m.faces))
m.export(__file__.replace('.py', '_uso.stl'))           # orientato come in uso (per verifiche/render)
np.save(__file__.replace('.py', '_T.npy'), T)
# orientamento di stampa: faccia superiore del ripiano sul piatto (y_A verso il basso)
P = np.eye(4); P[:3, :3] = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]]) @ R.T
s = m.copy(); s.apply_transform(P); s.apply_translation([0, 0, -s.bounds[0][2]])
s.export(__file__.replace('.py', '.stl'))
