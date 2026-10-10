"""Orthographic line views of an STL (print orientation, mm) with Blender Freestyle.

Writes <out>/<name>_front.png, _top.png, _left.png at an exact scale (300 dpi x scale) and
<out>/<name>.json with the bounding box. Visible edges solid, hidden edges dashed.
    blender-python draw_views.py -- part.stl outdir scale
"""
import bpy, sys, os, json, math
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
STL, OUT, SCALE = argv[0], argv[1], float(argv[2])
DPI = 300.0
PXMM = DPI / 25.4 * SCALE
MARGIN = 3.0
name = os.path.splitext(os.path.basename(STL))[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.wm.stl_import(filepath=STL)
ob = bpy.context.selected_objects[0]
me = ob.data
xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]
# longest horizontal side along x
if max(ys) - min(ys) > max(xs) - min(xs) + 0.01:
    from mathutils import Matrix
    me.transform(Matrix.Rotation(math.pi / 2, 4, 'Z'))
xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
lo = Vector((min(xs), min(ys), min(zs))); hi = Vector((max(xs), max(ys), max(zs)))
me.transform(__import__('mathutils').Matrix.Translation(-(lo + hi) / 2))
size = hi - lo
for p in me.polygons:
    p.use_smooth = False

mat = bpy.data.materials.new('w'); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1, 1, 1, 1)
out = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0], out.inputs[0])
me.materials.append(mat)
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 1, 1, 1)

sc.render.engine = 'CYCLES'
sc.cycles.samples = 1
sc.cycles.use_denoising = False
sc.view_settings.view_transform = 'Standard'
sc.render.use_freestyle = True
sc.render.line_thickness_mode = 'ABSOLUTE'
sc.render.line_thickness = 1.0
vl = sc.view_layers[0]
vl.use_freestyle = True
fs = vl.freestyle_settings
fs.crease_angle = math.radians(145)
for ls in list(fs.linesets):
    fs.linesets.remove(ls)


def lineset(nm, vis, thick, color, dashed):
    ls = fs.linesets.new(nm)
    ls.select_by_visibility = True
    ls.visibility = vis
    ls.select_by_edge_types = True
    ls.select_silhouette = True
    ls.select_border = True
    ls.select_crease = True
    ls.select_external_contour = True
    st = ls.linestyle
    st.color = color
    st.thickness = thick
    st.use_dashed_line = dashed
    if dashed:
        st.dash1, st.gap1 = 10, 7
    return ls


lineset('vis', 'VISIBLE', 3.2, (0, 0, 0), False)
lineset('hid', 'HIDDEN', 1.6, (0.45, 0.45, 0.45), True)

cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.sensor_fit = 'HORIZONTAL'
cd.clip_start, cd.clip_end = 0.1, 5000
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
views = {  # name: (camera direction from the part, horizontal extent, vertical extent, up)
    'front': (Vector((0, -1, 0)), size.x, size.z),
    'top': (Vector((0, 0, 1)), size.x, size.y),
    'left': (Vector((-1, 0, 0)), size.y, size.z),
}
info = {'name': name, 'size': [size.x, size.y, size.z], 'scale': SCALE, 'views': {}}
for vn, (d, wmm, hmm) in views.items():
    W, H = wmm + 2 * MARGIN, hmm + 2 * MARGIN
    cd.ortho_scale = W
    sc.render.resolution_x = max(8, round(W * PXMM))
    sc.render.resolution_y = max(8, round(H * PXMM))
    sc.render.resolution_percentage = 100
    cam.location = d * 1000
    up = Vector((0, 1, 0)) if vn == 'top' else Vector((0, 0, 1))
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler() if vn != 'top' else (0, 0, 0)
    sc.render.filepath = os.path.join(OUT, f'{name}_{vn}.png')
    bpy.ops.render.render(write_still=True)
    info['views'][vn] = {'w_mm': W, 'h_mm': H, 'px': [sc.render.resolution_x, sc.render.resolution_y]}
json.dump(info, open(os.path.join(OUT, f'{name}.json'), 'w'), indent=1)
