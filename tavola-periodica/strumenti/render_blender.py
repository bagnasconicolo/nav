"""Render fotorealistici con Blender (Cycles) per presentazioni.

Si lancia con:
  blender -b -P strumenti/render_blender.py -- tavola  USCITA.png [dettaglio]
  blender -b -P strumenti/render_blender.py -- esploso USCITA.png PUNTI.json

"tavola" usa gli STL di stl/ (prima: python3 strumenti/tavola.py esporta tutti).
"esploso" usa i pezzi preparati da strumenti/pitch.py, che poi aggiunge le
didascalie usando le coordinate in pixel salvate in PUNTI.json.

Coordinate come nel modello OpenSCAD: X a destra, Y dal fronte (0) verso il
retro, Z in alto. I cubi vengono colorati come escono dalla stampa a cambio
filamento: corpo scuro, lastra frontale chiara, testi e marker scuri.
"""
import json
import math
import os
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "strumenti"))
import tavola  # noqa: E402

Q = tavola.quote_dal_modello()
LATO, PROF, CORNICE = Q["lato"], Q["profondita"], Q["cornice"]
PASSO = LATO + tavola.GIOCO_PANNELLO
TMP = os.environ.get("RENDER_TMP", "/tmp/render_tavola")


# ---------------------------------------------------------------------------
# Scena, materiali, luci
# ---------------------------------------------------------------------------
def scena_vuota():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = int(os.environ.get("CAMPIONI", "256"))
    s.cycles.use_denoising = False   # il Blender di Debian non ha OpenImageDenoise
    s.cycles.sample_clamp_indirect = 3.0
    s.view_settings.view_transform = "AgX" if "AgX" in [
        v.identifier for v in s.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
    s.view_settings.look = "None"
    w = bpy.data.worlds.new("mondo")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.02, 0.022, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    s.world = w
    return s


def materiale(nome, rgb, ruvido=0.6, metallo=0.0):
    m = bpy.data.materials.get(nome)
    if m:
        return m
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*srgb(rgb), 1)
    p.inputs["Roughness"].default_value = ruvido
    p.inputs["Metallic"].default_value = metallo
    return m


def srgb(h):
    """#rrggbb -> lineare."""
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


MAT = {}


def materiali():
    MAT["corpo"] = materiale("corpo", "#26282b", 0.62)
    MAT["fronte"] = materiale("fronte", "#e8e4dc", 0.55)
    MAT["testo"] = materiale("testo", "#1c1d1f", 0.5)
    MAT["pannello"] = materiale("pannello", "#0a0a0b", 0.75)
    MAT["acciaio"] = materiale("acciaio", "#b9bcc0", 0.3, 1.0)
    MAT["ottone"] = materiale("ottone", "#c9a24f", 0.3, 1.0)


def luce_area(nome, pos, verso, forza, dim, colore=(1, 1, 1)):
    d = bpy.data.lights.new(nome, "AREA")
    d.energy = forza
    d.size = dim
    d.color = colore
    o = bpy.data.objects.new(nome, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = Vector(pos)
    o.rotation_euler = (Vector(verso) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    return o


def luci(centro, scala):
    c = Vector(centro)
    scala_luce = float(os.environ.get("LUCE", "1"))
    k = 6.0 * scala_luce
    # luce principale grande e morbida in alto a sinistra, riempimento a destra, controluce
    luce_area("chiave", c + Vector((-1.2, -1.6, 1.3)) * scala, c, k * 5.5e6 * (scala / 1000) ** 2, scala * 0.9)
    luce_area("riempimento", c + Vector((1.5, -1.2, 0.2)) * scala, c, k * 1.2e6 * (scala / 1000) ** 2, scala * 1.2)
    luce_area("taglio", c + Vector((0.3, 0.4, 1.6)) * scala, c, k * 1.5e6 * (scala / 1000) ** 2, scala * 0.6,
              (1.0, 0.96, 0.9))


def camera(pos, mira, focale=85, larghezza=2400, altezza=1500):
    s = bpy.context.scene
    d = bpy.data.cameras.new("camera")
    d.lens = focale
    d.clip_end = 100000
    o = bpy.data.objects.new("camera", d)
    s.collection.objects.link(o)
    o.location = Vector(pos)
    o.rotation_euler = (Vector(mira) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    s.camera = o
    s.render.resolution_x, s.render.resolution_y = larghezza, altezza
    s.render.resolution_percentage = int(os.environ.get("PERCENTUALE", "100"))
    return o


def inquadra(cam, mira, punti, margine=1.08):
    """Avvicina o allontana la camera dal punto mirato finché i punti riempiono il fotogramma."""
    s = bpy.context.scene
    mira = Vector(mira)
    for _ in range(12):
        bpy.context.view_layer.update()
        uv = [world_to_camera_view(s, cam, Vector(p)) for p in punti]
        asp = s.render.resolution_x / s.render.resolution_y
        fuori = max(max(abs(u.x - 0.5) * 2, abs(u.y - 0.5) * 2) for u in uv)
        if abs(fuori * margine - 1) < 0.005:
            break
        cam.location = mira + (cam.location - mira) * (fuori * margine)


# ---------------------------------------------------------------------------
# Cubi: STL -> oggetto Blender con i tre colori della stampa
# ---------------------------------------------------------------------------
def importa_stl(percorso):
    bpy.ops.wm.stl_import(filepath=percorso)
    return bpy.context.selected_objects[0]


def cubo(percorso, offset=(0, 0, 0), stampa=True):
    o = importa_stl(percorso)
    if stampa:
        # STL di stampa (retro sul piatto): (X, Y, Z) -> (X, PROF - Z, Y)
        o.data.transform(Matrix(((1, 0, 0, 0), (0, 0, -1, PROF), (0, 1, 0, 0), (0, 0, 0, 1))))
    colora_cubo(o)
    o.location = Vector(offset)
    return o


def colora_cubo(o):
    """Taglia la mesh ai piani y = 0 e y = CORNICE e assegna i tre materiali."""
    me = o.data
    for m in (MAT["corpo"], MAT["fronte"], MAT["testo"]):
        me.materials.append(m)
    bm = bmesh.new()
    bm.from_mesh(me)
    for y in (0.0, CORNICE):
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, y, 0), plane_no=(0, 1, 0))
    for f in bm.faces:
        y = f.calc_center_median().y
        f.material_index = 2 if y < -0.02 else 1 if y < CORNICE - 0.02 else 0
        f.smooth = False
    bm.to_mesh(me)
    bm.free()


def oggetto_materiale(o, chiave):
    o.data.materials.clear()
    o.data.materials.append(MAT[chiave])


def scatola(nome, x0, y0, z0, x1, y1, z1, chiave):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = nome
    o.scale = (x1 - x0, y1 - y0, z1 - z0)
    o.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    oggetto_materiale(o, chiave)
    return o


def cilindro_y(nome, x, z, y0, y1, d, chiave, d2=None, lati=64):
    """Cilindro (o tronco di cono se d2) lungo Y, da y0 a y1."""
    bpy.ops.mesh.primitive_cone_add(vertices=lati, radius1=d / 2, radius2=(d2 if d2 is not None else d) / 2,
                                    depth=abs(y1 - y0))
    o = bpy.context.active_object
    o.name = nome
    o.rotation_euler = (math.radians(-90 if y1 > y0 else 90), 0, 0)
    o.location = (x, (y0 + y1) / 2, z)
    oggetto_materiale(o, chiave)
    bpy.ops.object.shade_smooth()
    return o


# ---------------------------------------------------------------------------
# Scena 1: la tavola completa su pannello nero
# ---------------------------------------------------------------------------
def scena_tavola(uscita, dettaglio=False):
    scena_vuota()
    materiali()
    cubi = tavola.con_vicini(tavola.tutti_i_cubi())
    righe = max(c["riga"] for c in cubi)
    colonne = max(c["colonna"] for c in cubi)
    W, H = colonne * PASSO, righe * PASSO
    bordo = 60
    for c in cubi:
        p = os.path.join(tavola.DIR_STL, c["id"] + ".stl")
        cubo(p, ((c["colonna"] - 1) * PASSO, 0, (righe - c["riga"]) * PASSO))
    scatola("pannello", -bordo, PROF, -bordo, W + bordo, PROF + 18, H + bordo, "pannello")
    # muro dietro, appena più chiaro del pannello: dà profondità all'ombra
    scatola("muro", -5000, PROF + 18, -5000, 5000, PROF + 40, 5000, "pannello")
    centro = (W / 2, 0, H / 2)
    luci(centro, 2200)
    if dettaglio:
        # gruppo ravvicinato: periodi 4-6, gruppi 8-12 (Fe ... Hg)
        x0, x1 = 7 * PASSO, 12 * PASSO
        z0, z1 = (righe - 6) * PASSO, (righe - 3) * PASSO
        m = ((x0 + x1) / 2, 0, (z0 + z1) / 2)
        cam = camera((m[0] - 380, -900, m[2] + 260), m, focale=100)
        inquadra(cam, m, [(x0, 0, z0), (x1, 0, z1), (x0, 0, z1), (x1, 0, z0)], 1.02)
    else:
        mira = (W / 2, 0, H / 2 - 20)
        cam = camera((W * 0.5 - 900, -3300, H * 0.5 + 700), mira, focale=70)
        inquadra(cam, mira, [(-bordo, PROF, -bordo), (W + bordo, PROF, H + bordo),
                             (-bordo, PROF, H + bordo), (W + bordo, PROF, -bordo)], 1.06)
    bpy.context.scene.render.filepath = uscita
    bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------------------
# Scena 2: esploso di un cubo, con viteria e pannello
# ---------------------------------------------------------------------------
def scena_esploso(uscita, punti_json):
    scena_vuota()
    materiali()
    with open(os.path.join(TMP, "pezzi.json")) as f:
        info = json.load(f)
    vx, vz = Q["vite"]
    sx, sz = Q["spina"]
    y_tappo, d_tappo, h_tappo = Q["tappo"]
    sp = {"pannello": 0, "cubo": -75, "vite": -150, "tappo": -185}   # spostamenti lungo Y
    # pannello (spaccato) con inserto filettato e spina
    scatola("pannello", -18, PROF, -18, LATO + 18, PROF + 18, LATO + 18, "pannello")
    cilindro_y("inserto", vx, vz, PROF + 0.2, PROF + 9, 5.0, "ottone")
    cilindro_y("inserto_flangia", vx, vz, PROF - 0.6, PROF + 0.2, 6.6, "ottone")
    cilindro_y("spina", sx, sz, PROF - 3, PROF + 9, 4.0, "acciaio")
    # cubo
    c = cubo(info["cubo"], (0, sp["cubo"], 0), stampa=False)
    # vite M3x12 a testa svasata: testa a filo del mozzo
    yv = y_tappo + h_tappo + sp["vite"]
    cilindro_y("vite_testa", vx, vz, yv, yv + 1.75, 6.0, "acciaio", d2=3.0)
    cilindro_y("vite_gambo", vx, vz, yv + 1.75, yv + 12, 3.0, "acciaio")
    # tappino
    t = importa_stl(info["tappo"])
    t.rotation_euler = (math.radians(-90), 0, 0)
    t.location = (vx, y_tappo + sp["tappo"], vz)
    oggetto_materiale(t, "corpo")
    # assi di montaggio tratteggiati: sottili cilindri chiari
    for (x, z, ya, yb) in [(vx, vz, sp["tappo"] + y_tappo - 6, PROF), (sx, sz, sp["cubo"] + PROF - 6, PROF)]:
        y = ya
        while y < yb:
            cilindro_y("asse", x, z, y, min(y + 2.5, yb), 0.35, "fronte", lati=12)
            y += 5
    centro = (LATO / 2, -60, LATO / 2)
    os.environ["LUCE"] = str(0.45 * float(os.environ.get("LUCE", "1")))   # il corpo deve restare scuro
    luci(centro, 480)
    # controluce dal retro a destra: disegna i bordi del corpo scuro sul fondo nero
    luce_area("bordo", (LATO + 160, PROF + 120, LATO + 120), centro, 5.0e6 * float(os.environ.get("LUCE", "1")),
              120, (0.85, 0.9, 1.0))
    mira = (LATO / 2 - 4, -55, LATO / 2 + 24)
    cam = camera((-330, -250, LATO + 170), mira, focale=50, larghezza=2400, altezza=1600)
    inquadra(cam, mira, [(vx, sp["tappo"] + y_tappo, vz), (LATO + 18, PROF + 18, LATO + 18),
                         (0, sp["cubo"], 0), (LATO + 18, PROF, -18), (0, sp["cubo"], LATO)], 1.4)
    bpy.context.view_layer.update()
    # punti da annotare, in coordinate del cubo (poi spostate come i pezzi)
    s = bpy.context.scene
    dy = sp["cubo"]
    punti = {
        "linguetta": (LATO / 2, dy + 18, LATO + 1),
        "finestra_sopra": (LATO * 0.3, dy + 30, LATO),
        "fuga": (LATO - 1.2, dy + 0.5, LATO - 1.2),
        "vite": (vx, sp["vite"] + y_tappo + 6, vz),
        "tappo": (vx, sp["tappo"] + y_tappo, vz + 3.5),
        "inserto": (vx, PROF - 0.6, vz + 3.3),
        "spina": (sx, PROF - 3, sz + 2),
        "pannello": (LATO + 10, PROF, LATO + 10),
    }
    salva(cam, punti, punti_json, uscita)


def salva(cam, punti, punti_json, uscita):
    """Proietta i punti da annotare in pixel, poi fa il render."""
    s = bpy.context.scene
    bpy.context.view_layer.update()
    px = {}
    for k, p in punti.items():
        u = world_to_camera_view(s, cam, Vector(p))
        px[k] = (u.x * s.render.resolution_x, (1 - u.y) * s.render.resolution_y)
    with open(punti_json, "w") as f:
        json.dump(px, f, indent=1)
    s.render.filepath = uscita
    bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------------------
# Scena 3: il cubo montato, quasi di fronte, per spiegare la targhetta
# ---------------------------------------------------------------------------
def scena_fronte(uscita, punti_json):
    scena_vuota()
    materiali()
    with open(os.path.join(TMP, "pezzi.json")) as f:
        info = json.load(f)
    vx, vz = Q["vite"]
    y_tappo, _, _ = Q["tappo"]
    cubo(info["cubo"], (0, 0, 0), stampa=False)
    t = importa_stl(info["tappo"])
    t.rotation_euler = (math.radians(-90), 0, 0)
    t.location = (vx, y_tappo, vz)
    oggetto_materiale(t, "corpo")
    scatola("pannello", -400, PROF, -400, LATO + 400, PROF + 18, LATO + 400, "pannello")
    centro = (LATO / 2, 0, LATO / 2)
    os.environ["LUCE"] = str(0.75 * float(os.environ.get("LUCE", "1")))
    luci(centro, 400)
    mira = (LATO / 2 + 4, 10, LATO / 2 - 6)
    cam = camera((-45, -340, LATO + 45), mira, focale=70, larghezza=2400, altezza=1600)
    inquadra(cam, mira, [(0, 0, 0), (LATO, 0, LATO), (0, 0, LATO), (LATO, 0, 0)], 1.7)
    punti = {
        "simbolo": (9, -0.6, 5.2),
        "numero": (LATO - 18.5, -0.6, 4.5),
        "marker": (LATO - 6 - 3.3, -0.6, 5.2),
        "fronte": (0.6, -0.3, LATO * 0.62),
        "nicchia": (LATO * 0.78, PROF - 2, LATO * 0.35),
        "tappo": (vx, y_tappo, vz),
    }
    salva(cam, punti, punti_json, uscita)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    if argv[0] == "tavola":
        scena_tavola(argv[1], dettaglio=len(argv) > 2 and argv[2] == "dettaglio")
    elif argv[0] == "esploso":
        scena_esploso(argv[1], argv[2])
    elif argv[0] == "fronte":
        scena_fronte(argv[1], argv[2])
