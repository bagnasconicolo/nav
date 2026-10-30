# Tappo scorrevole per il collare superiore di case-ampoules_rigido:
# entra con gioco nell'anello Ø31, costola che scorre nella fessura posteriore (fa anche da finecorsa),
# foro guida centrale sotto per avvitare direttamente una vite 1/4"-20 nella plastica.
import trimesh, numpy as np
from trimesh.creation import cylinder, box

R_COLLAR = 15.5           # raggio interno collare (Ø31)
GIOCO_D  = 0.30           # gioco diametrale: scorre ma non "corre" (0.2 = più duro, 0.4 = più libero)
H_TAPPO  = 18.0           # altezza corpo
SLOT_W   = 3.0            # larghezza fessura nel collare
GIOCO_C  = 0.15           # gioco per lato della costola
R_COSTOLA = 19.0          # fin dove sporge la costola (esterno collare = 19.5)
H_COSTOLA = 6.0           # alta 6 mm, in cima al tappo (il tappo può scendere 13-6 = 7 mm sotto il bordo)
D_FORO    = 5.4           # foro guida per vite 1/4"-20 autofilettante nella plastica (5.2 = più presa, 5.6 = più facile)
P_FORO    = 15.0          # profondità foro (lascia 3 mm di fondo)
SMUSSO    = 0.6
SEC = 160

r = R_COLLAR - GIOCO_D/2
def frustum(r0, r1, z0, z1):
    a = np.linspace(0, 2*np.pi, SEC, endpoint=False)
    return trimesh.convex.convex_hull(np.vstack([
        np.c_[r0*np.cos(a), r0*np.sin(a), np.full(SEC, z0)],
        np.c_[r1*np.cos(a), r1*np.sin(a), np.full(SEC, z1)]]))
def bx(x0, x1, y0, y1, z0, z1):
    b = box(extents=[x1-x0, y1-y0, z1-z0]); b.apply_translation([(x0+x1)/2, (y0+y1)/2, (z0+z1)/2]); return b

# corpo con smusso sullo spigolo inferiore (invito d'ingresso)
body = trimesh.boolean.union([frustum(r-SMUSSO, r, 0, SMUSSO), frustum(r, r, SMUSSO, H_TAPPO)])
# costola sul retro (-x), in cima al tappo, con smusso sotto per imboccare la fessura
w = SLOT_W - 2*GIOCO_C
cost = bx(-R_COSTOLA, -(r-1.0), -w/2, w/2, H_TAPPO-H_COSTOLA, H_TAPPO)
cut = trimesh.creation.extrude_polygon(
    __import__('shapely').geometry.Polygon([(-R_COSTOLA-1, H_TAPPO-H_COSTOLA-0.01), (-r, H_TAPPO-H_COSTOLA-0.01),
                                           (-R_COSTOLA-1, H_TAPPO-H_COSTOLA+(R_COSTOLA+1-r))]), w+2)
cut.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0])); cut.apply_translation([0, (w+2)/2, 0])
cost = cost.difference(cut)
body = trimesh.boolean.union([body, cost])
# foro guida 1/4" al centro della faccia inferiore, con invito
foro = trimesh.boolean.union([frustum(D_FORO/2, D_FORO/2, -1, P_FORO),
                              frustum(6.6/2, D_FORO/2, -0.01, (6.6-D_FORO)/2)])
body = body.difference(foro)
print(body.is_watertight, body.bounds.round(2).tolist(), round(body.volume, 1))
# orientato per la stampa: faccia superiore sul piatto, foro verso l'alto
body.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
body.apply_translation([0, 0, -body.bounds[0][2]])
body.export(__file__.replace('.py', '.stl'))
