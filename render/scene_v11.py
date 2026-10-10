import bpy, bmesh, math, sys
from mathutils import Vector

RES = int(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else 800
SAMPLES = int(sys.argv[sys.argv.index('--') + 2]) if '--' in sys.argv else 64
OUT = sys.argv[sys.argv.index('--') + 3] if '--' in sys.argv else '/tmp/r.png'
MODE = sys.argv[sys.argv.index('--') + 4] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 4 else 'assembled'
EXPLODED = MODE == 'exploded'
PARTS = MODE == 'parts'
OPEN = MODE == 'compute_open'
COMPUTE_VIEW = MODE in ('compute', 'compute_open')
from mathutils import Matrix

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
MM = 0.001


def m(v):
    return v * MM


# ---------------------------------------------------------------- helpers
def mesh_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def box(name, x0, x1, y0, y1, z0, z1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = m(x0) if v.co.x < 0 else m(x1)
        v.co.y = m(y0) if v.co.y < 0 else m(y1)
        v.co.z = m(z0) if v.co.z < 0 else m(z1)
    return mesh_obj(name, bm)


def prism(name, pts_xy, z0, z1, axis='z'):
    """Extrude a 2D polygon (mm) between z0 and z1 along the given axis."""
    bm = bmesh.new()
    def mk(a, b, c):
        if axis == 'z':
            return bm.verts.new((m(a), m(b), m(c)))
        if axis == 'x':
            return bm.verts.new((m(c), m(a), m(b)))
        if axis == 'y':
            return bm.verts.new((m(a), m(c), m(b)))
    bot = [mk(x, y, z0) for x, y in pts_xy]
    top = [mk(x, y, z1) for x, y in pts_xy]
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    n = len(pts_xy)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([bot[i], bot[j], top[j], top[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm)


def cyl(name, cx, cy, r, z0, z1, seg=48, axis='z'):
    pts = [(cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    return prism(name, pts, z0, z1, axis)


def apply_mods(ob):
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
        for md in list(ob.modifiers):
            bpy.ops.object.modifier_apply(modifier=md.name)


def boolean(target, cutter, op='DIFFERENCE'):
    md = target.modifiers.new('b', 'BOOLEAN')
    md.operation = op
    md.solver = 'EXACT'
    md.object = cutter
    apply_mods(target)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return target


def bevel(ob, w, seg=2, angle=40):
    md = ob.modifiers.new('bev', 'BEVEL')
    md.width = m(w)
    md.segments = seg
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(angle)
    md.harden_normals = False
    apply_mods(ob)
    return ob


def smooth(ob, angle=35):
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.shade_auto_smooth(angle=math.radians(angle))


def mirror_x(ob, name):
    new = ob.copy()
    new.data = ob.data.copy()
    new.name = name
    scene.collection.objects.link(new)
    for v in new.data.vertices:
        v.co.x = -v.co.x
    new.data.flip_normals()
    return new


# ---------------------------------------------------------------- materials
def node_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    return mat, nt, bsdf


def mat_printed(name, color, rough, layer_period_mm=0.25, bump=0.25):
    mat, nt, bsdf = node_mat(name)
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = rough
    tc = nt.nodes.new('ShaderNodeTexCoord')
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'
    wave.bands_direction = 'Z'
    wave.inputs['Scale'].default_value = 0.6283 / (layer_period_mm * MM)
    wave.inputs['Distortion'].default_value = 0.0
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 900
    mix = nt.nodes.new('ShaderNodeMath')
    mix.operation = 'MULTIPLY_ADD'
    mix.inputs[1].default_value = 1.0
    nt.links.new(tc.outputs['Object'], wave.inputs['Vector'])
    nt.links.new(tc.outputs['Object'], noise.inputs['Vector'])
    nt.links.new(wave.outputs['Fac'], mix.inputs[0])
    nt.links.new(noise.outputs['Fac'], mix.inputs[2])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = bump
    bp.inputs['Distance'].default_value = m(0.03)
    nt.links.new(mix.outputs[0], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def mat_foil():
    mat, nt, bsdf = node_mat('foil')
    bsdf.inputs['Base Color'].default_value = (0.70, 0.71, 0.72, 1)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.34
    tc = nt.nodes.new('ShaderNodeTexCoord')
    # stretched mapping so creases run mostly across the bar
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0, 3.0, 1.0)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'X'
    wv.wave_profile = 'SIN'
    wv.inputs['Scale'].default_value = 9
    wv.inputs['Distortion'].default_value = 9
    wv.inputs['Detail'].default_value = 3
    wv.inputs['Detail Scale'].default_value = 1.5
    nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 70
    noise.inputs['Detail'].default_value = 8
    noise.inputs['Roughness'].default_value = 0.6
    nt.links.new(tc.outputs['Object'], noise.inputs['Vector'])
    add = nt.nodes.new('ShaderNodeMath')
    add.operation = 'MULTIPLY_ADD'
    add.inputs[1].default_value = 0.35
    nt.links.new(noise.outputs['Fac'], add.inputs[0])
    nt.links.new(wv.outputs['Fac'], add.inputs[2])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.18
    bp.inputs['Distance'].default_value = m(0.25)
    nt.links.new(add.outputs[0], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
    # slight roughness variation
    rr = nt.nodes.new('ShaderNodeMapRange')
    rr.inputs['To Min'].default_value = 0.30
    rr.inputs['To Max'].default_value = 0.40
    nt.links.new(noise.outputs['Fac'], rr.inputs['Value'])
    nt.links.new(rr.outputs['Result'], bsdf.inputs['Roughness'])
    return mat


def mat_alu():
    mat, nt, bsdf = node_mat('alu')
    bsdf.inputs['Base Color'].default_value = (0.74, 0.75, 0.77, 1)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.30
    bsdf.inputs['Anisotropic'].default_value = 0.5
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (400, 400, 4)
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 3
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], noise.inputs['Vector'])
    rr = nt.nodes.new('ShaderNodeMapRange')
    rr.inputs['To Min'].default_value = 0.36
    rr.inputs['To Max'].default_value = 0.44
    nt.links.new(noise.outputs['Fac'], rr.inputs['Value'])
    nt.links.new(rr.outputs['Result'], bsdf.inputs['Roughness'])
    tan = nt.nodes.new('ShaderNodeTangent')
    tan.direction_type = 'RADIAL'
    tan.axis = 'Z'
    nt.links.new(tan.outputs['Tangent'], bsdf.inputs['Tangent'])
    return mat


def mat_simple(name, color, rough, metal=0.0, coat=0.0):
    mat, nt, bsdf = node_mat(name)
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Coat Weight'].default_value = coat
    return mat


M_BASE = mat_printed('anthracite', (0.032, 0.034, 0.038), 0.52, 0.25, 0.3)
M_CLIP = mat_printed('clip_orange', (0.40, 0.085, 0.010), 0.58, 0.2, 0.25)
M_FOIL = mat_foil()
M_ALU = mat_alu()
M_PCB = mat_simple('pcb', (0.015, 0.16, 0.045), 0.28, coat=0.4)
M_TERM = mat_simple('terminal', (0.02, 0.02, 0.022), 0.42)
M_SCREW = mat_simple('screw', (0.8, 0.8, 0.78), 0.25, metal=1.0)
M_TIN = mat_simple('tin', (0.85, 0.85, 0.85), 0.2, metal=1.0)
M_IC = mat_simple('ic', (0.02, 0.02, 0.022), 0.45)
M_CAP = mat_simple('cap', (0.45, 0.30, 0.15), 0.4)
M_RES = mat_simple('res', (0.03, 0.03, 0.03), 0.35)
M_SPACER = M_BASE
M_CAP_TOP = mat_simple('endcap', (0.025, 0.025, 0.028), 0.5)
M_WIRE_R = mat_simple('wire_red', (0.45, 0.012, 0.01), 0.38)
M_WIRE_K = mat_simple('wire_black', (0.012, 0.012, 0.014), 0.38)
M_BOLT = mat_simple('bolt', (0.05, 0.05, 0.055), 0.32, metal=1.0)
M_RUBBER = mat_simple('rubber', (0.012, 0.012, 0.012), 0.85)
M_SHEATH = mat_printed('sheath', (0.012, 0.012, 0.013), 0.5, 0.6, 0.6)
M_SHRINK = mat_simple('shrink', (0.01, 0.01, 0.011), 0.28)
M_NYLON = mat_simple('kk_nylon', (0.80, 0.76, 0.64), 0.5)
M_COAX = mat_simple('coax', (0.012, 0.012, 0.013), 0.42)
M_ACRYL = bpy.data.materials.new('acrylic')
M_ACRYL.use_nodes = True
_b = M_ACRYL.node_tree.nodes['Principled BSDF']
_b.inputs['Base Color'].default_value = (0.86, 0.93, 0.95, 1)
_b.inputs['Roughness'].default_value = 0.04
_b.inputs['IOR'].default_value = 1.49
_b.inputs['Transmission Weight'].default_value = 1.0
M_HOLE = mat_simple('dark', (0.01, 0.01, 0.01), 0.8)


def setmat(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


# ---------------------------------------------------------------- geometry
BAR_L, BAR_W, BAR_T = 300.0, 45.0, 5.0
BAR_Z = [60.0, 130.0, 200.0]
CLR = 0.5             # clearance in pocket
POCKET_D = 10.5       # pocket depth from mouth
WALL_YZ = 2.4         # pocket side/top/bottom walls
BACK = 3.5            # back wall thickness
X_MOUTH = -BAR_L / 2 + 10.0             # -140
X_BOTTOM = X_MOUTH - POCKET_D           # -150.5
X_BACK = X_BOTTOM - BACK                # -154 : clip back face = upright inner face
UP = 20.0
UX = X_BACK - UP / 2                    # upright centre x
FOOT_H = 10.0
SOCK_TOP = 30.0
UP_Z0 = 8.0
UP_H = 250.0

# slot geometry (depth measured from the face)
SL_OPEN = 3.0     # half opening
SL_LIP = 1.8
SL_CAV = 5.6      # half width of cavity under lips
SL_DEPTH = 6.0
SL_BOT = 2.4      # half width at cavity bottom


def text_obj(name, body, size, depth, mat):
    """Extruded text (mm), centred on the origin, lying in XY, thickness `depth` along Z."""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = m(size)
    cu.extrude = m(depth / 2)
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.resolution_u = 8
    tmp = bpy.data.objects.new(name, cu)
    scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    setmat(ob, mat)
    return ob


def make_upright(name, cx, zb=UP_Z0, h=UP_H):
    up = box(name, cx - UP / 2, cx + UP / 2, -UP / 2, UP / 2, zb, zb + h)
    bevel(up, 0.6, 3)
    z0, z1 = zb - 2, zb + h + 2
    for k in range(4):
        ang = k * math.pi / 2
        # local slot profile: u across the face, d = depth into profile
        loc = [(-SL_OPEN, -2.0), (-SL_OPEN, SL_LIP), (-SL_CAV, SL_LIP), (-SL_BOT, SL_DEPTH),
               (SL_BOT, SL_DEPTH), (SL_CAV, SL_LIP), (SL_OPEN, SL_LIP), (SL_OPEN, -2.0)]
        pts = []
        for u, d in loc:
            # face normal along +x rotated by ang; face at distance UP/2
            r = UP / 2 - d
            nx, ny = math.cos(ang), math.sin(ang)
            tx, ty = -ny, nx
            pts.append((cx + nx * r + tx * u, ny * r + ty * u))
        cut = prism('slot', pts, z0, z1)
        boolean(up, cut)
    boolean(up, cyl('bore', cx, 0, 2.1, z0, z1, 32))
    setmat(up, M_ALU)
    smooth(up, 30)
    return up


def make_clip(name, zc):
    hw = BAR_W / 2 + CLR + WALL_YZ
    hh = BAR_T / 2 + CLR + WALL_YZ
    body = box(name, X_BACK, X_MOUTH, -hw, hw, zc - hh, zc + hh)
    # back plate, taller, carries the T tongue
    bevel(body, 2.2, 4)
    plate = box('plate', X_BACK, X_BOTTOM + 1.0, -13, 13, zc - 10, zc + 10)
    bevel(plate, 1.6, 3)
    boolean(body, plate, 'UNION')
    pocket = box('pocket', X_BOTTOM, X_MOUTH + 2, -BAR_W / 2 - CLR, BAR_W / 2 + CLR,
                 zc - BAR_T / 2 - CLR, zc + BAR_T / 2 + CLR)
    boolean(body, pocket)
    # lead-in chamfer at the pocket mouth
    ch = 0.9
    bm = bmesh.new()
    py, pz = BAR_W / 2 + CLR, BAR_T / 2 + CLR
    vs = []
    for x, e in ((X_MOUTH - ch, 0.0), (X_MOUTH + 0.5, ch + 0.5)):
        for y, z in ((-py - e, zc - pz - e), (py + e, zc - pz - e), (py + e, zc + pz + e), (-py - e, zc + pz + e)):
            vs.append(bm.verts.new((m(x), m(y), m(z))))
    bm.faces.new(vs[0:4]); bm.faces.new(vs[4:8])
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([vs[i], vs[j], vs[4 + j], vs[4 + i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    boolean(body, mesh_obj('mouth', bm))
    # T tongue: neck through the slot opening, head behind the lips
    neck = box('neck', X_BACK - 2.0, X_BACK + 0.2, -2.5, 2.5, zc - 10, zc + 10)
    head = box('head', X_BACK - 4.0, X_BACK - 1.95, -3.7, 3.7, zc - 10, zc + 10)
    bevel(head, 0.3, 1)
    boolean(body, neck, 'UNION')
    boolean(body, head, 'UNION')
    setmat(body, M_CLIP)
    smooth(body, 35)
    return body


def make_bar(name, zc):
    bar = box(name, -BAR_L / 2, BAR_L / 2, -BAR_W / 2, BAR_W / 2, zc - BAR_T / 2, zc + BAR_T / 2)
    bevel(bar, 0.6, 3)
    setmat(bar, M_FOIL)
    smooth(bar, 35)
    return bar


PCB_PARTS = []
ENTRIES = []
COVERS = []


def make_pcb(zc):
    zt = zc + BAR_T / 2
    parts = PCB_PARTS
    x0, x1 = -BAR_L / 2 + 17.0, -BAR_L / 2 + 41.0   # -133 .. -109
    y0, y1 = -21.0, 8.0
    pcb = box('pcb', x0, x1, y0, y1, zt, zt + 1.6)
    bevel(pcb, 0.4, 1)
    setmat(pcb, M_PCB)
    parts.append(pcb)
    zp = zt + 1.6
    # --- Molex KK 254, 2 pins, right-angle header (22-05-3021 style) + crimp housing (22-01-3027 style)
    P = 2.54
    hx = -121.0                                   # header centre x
    pins_x = [hx - P / 2, hx + P / 2]
    tx0, tx1 = hx - 2.9, hx + 2.9                 # header body extents (used by the cover window)
    hb0, ty1 = y0 + 0.4, y0 + 3.6                 # header wall, y range (back)
    zpin = zp + 2.54
    hdr = box('kk_hdr', tx0, tx1, hb0, ty1, zp, zp + 6.2)
    bevel(hdr, 0.2, 1)
    # friction-lock ramp on the front face of the wall
    ramp = prism('ramp', [(hb0, zp + 4.4), (hb0 - 1.1, zp + 5.4), (hb0 - 1.1, zp + 6.2), (hb0, zp + 6.2)],
                 hx - 1.2, hx + 1.2, axis='x')
    boolean(hdr, ramp, 'UNION')
    setmat(hdr, M_NYLON)
    smooth(hdr, 30)
    parts.append(hdr)
    for px in pins_x:
        # square pin: horizontal part toward the front, bent down through the PCB at the back
        pin = box('kkpin', px - 0.32, px + 0.32, y0 - 9.5, ty1 + 1.6, zpin - 0.32, zpin + 0.32)
        setmat(pin, M_TIN); parts.append(pin)
        pin = box('kkpin', px - 0.32, px + 0.32, ty1 + 1.0, ty1 + 1.64, zp - 0.5, zpin + 0.32)
        setmat(pin, M_TIN); parts.append(pin)
    # crimp housing plugged on the pins, wires leave toward the front (-y)
    hs0, hs1 = y0 - 11.9, hb0 - 0.05
    hsg = box('kk_housing', hx - 2.5, hx + 2.5, hs0, hs1, zpin - 2.4, zpin + 2.4)
    bevel(hsg, 0.25, 1)
    # latch slot on top and wire entries at the front
    boolean(hsg, box('latch', hx - 1.0, hx + 1.0, hs1 - 7.5, hs1 - 1.5, zpin + 1.6, zpin + 3))
    for px in pins_x:
        boolean(hsg, box('went', px - 0.85, px + 0.85, hs0 - 1, hs0 + 2.0, zpin - 0.85, zpin + 0.85))
        boolean(hsg, box('cwin', px - 0.6, px + 0.6, hs0 + 3.5, hs0 + 7.5, zpin + 1.0, zpin + 3))
        ENTRIES.append((px, hs0, zpin, zc))
    setmat(hsg, M_NYLON)
    smooth(hsg, 30)
    parts.append(hsg)
    # --- SOIC-8
    ix0, iy0 = -131.0, -8.0
    ic = box('ic', ix0, ix0 + 5.0, iy0, iy0 + 4.0, zp + 0.15, zp + 1.6)
    bevel(ic, 0.15, 1)
    setmat(ic, M_IC)
    parts.append(ic)
    for i in range(4):
        px = ix0 + 0.6 + i * 1.27
        for ya, yb in [(iy0 - 0.9, iy0 + 0.1), (iy0 + 3.9, iy0 + 4.9)]:
            pin = box('pin', px - 0.22, px + 0.22, ya, yb, zp, zp + 0.5)
            setmat(pin, M_TIN)
            parts.append(pin)
    # --- 0805 passives (body + tinned terminations)
    def passive(cx, cy, mat, rot=False, h=0.55):
        L, W = 2.0, 1.25
        if rot:
            L, W = W, L
        b = box('smd', cx - L / 2, cx + L / 2, cy - W / 2, cy + W / 2, zp, zp + h)
        setmat(b, mat)
        parts.append(b)
        e = 0.35
        if not rot:
            ends = [(cx - L / 2 - 0.02, cx - L / 2 + e, cy - W / 2 - 0.02, cy + W / 2 + 0.02),
                    (cx + L / 2 - e, cx + L / 2 + 0.02, cy - W / 2 - 0.02, cy + W / 2 + 0.02)]
        else:
            ends = [(cx - L / 2 - 0.02, cx + L / 2 + 0.02, cy - W / 2 - 0.02, cy - W / 2 + e),
                    (cx - L / 2 - 0.02, cx + L / 2 + 0.02, cy + W / 2 - e, cy + W / 2 + 0.02)]
        for a, b2, c, d in ends:
            t = box('term', a, b2, c, d, zp, zp + h + 0.03)
            setmat(t, M_TIN)
            parts.append(t)
    passive(-122.5, -6.0, M_RES)
    passive(-118.0, -6.0, M_CAP, h=0.8)
    passive(-113.5, -6.0, M_RES)
    passive(-122.5, -1.5, M_CAP, h=0.8)
    passive(-114.5, 0.5, M_RES, rot=True)
    passive(-127.0, 3.0, M_CAP, h=0.8)
    # SOT-23
    s = box('sot', -120.0, -117.0, 1.6, 3.0, zp + 0.1, zp + 1.0)
    setmat(s, M_IC)
    parts.append(s)
    for px in [-119.45, -117.55]:
        pin = box('pin', px - 0.2, px + 0.2, 0.9, 1.7, zp, zp + 0.3)
        setmat(pin, M_TIN); parts.append(pin)
    pin = box('pin', -118.7, -118.3, 2.9, 3.7, zp, zp + 0.3)
    setmat(pin, M_TIN); parts.append(pin)
    # mounting pads / tinned via pads at the rear
    for px in [-130.5, -111.5]:
        pad = cyl('pad', px, 5.5, 1.2, zp - 0.02, zp + 0.04, 24)
        setmat(pad, M_TIN); parts.append(pad)
    cov = box('cover', x0 - 1.4, x1 + 1.4, y0 - 1.4, y1 + 1.4, zt, zp + 3.4)
    bevel(cov, 1.2, 3)
    boolean(cov, box('cin', x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, zt - 1, zp + 2.2))
    boolean(cov, box('win', tx0 - 0.5, tx1 + 0.5, y0 - 3, ty1 + 2.2, zt - 1, zp + 10))
    setmat(cov, M_BASE)
    smooth(cov, 35)
    COVERS.append(cov)
    return parts


H_LEN = 300.0                # horizontal Bosch profile, 20x20 x 300
H_Z0 = 6.0                   # its bottom face height
H_X = H_LEN / 2              # profile ends at x = +-150
BS_X = UX + 21.0             # M5 button screw (into slot nut) under the profile end
FX0, FX1 = UX - 24.0, UX + 30.0   # foot extent in x (longer inwards, to hold 16 mm of profile)
FOOT_TOP = SOCK_TOP
PIN_X, PIN_Y = UX + 18.0, 56.0   # locating pin of the board module, in the foot plate
FIL_R = 18.0                 # fillet radius between block and plate
CH_W, CH_D = 14.0, 3.0       # cable channel width / depth
SH_R = 3.4                   # braided sheath radius
SH_Y = -19.5                 # sheath axis y (in front of the left upright)


def make_foot(name):
    """Printed foot: plate + block with vertical socket (upright) and side pocket
    (horizontal profile). Symmetric, so the same part is used on both sides."""
    cx = UX
    R = FIL_R
    foot = prism(name, [(-75, 0), (75, 0), (75, 5), (20 + R, FOOT_H), (-20 - R, FOOT_H), (-75, 5)], FX0, FX1, axis='x')
    bevel(foot, 1.6, 3, angle=30)
    blk = box('blk', FX0, FX1, -20, 20, 0, FOOT_TOP)
    bevel(blk, 2.0, 3)
    boolean(foot, blk, 'UNION')
    # concave fillets block -> plate, full width
    for sy in (-1, 1):
        pts = [(sy * 19.5, FOOT_H - 1)]
        for k in range(17):
            t = math.radians(90 * k / 16)
            pts.append((sy * (20 + R - R * math.cos(t)), FOOT_H + R - R * math.sin(t)))
        pts.append((sy * (20 + R + 0.5), FOOT_H - 1))
        if sy < 0:
            pts = pts[::-1]
        g = prism('fil', pts, FX0 + 1.0, FX1 - 1.0, axis='x')
        boolean(foot, g, 'UNION')
    # cable channel: down the front fillet and along the plate to the front edge
    d = CH_D
    pts = [(-15.5, 45), (-15.5, FOOT_H + R - math.sqrt(max((R + d) ** 2 - (R + 4.5) ** 2, 0)))]
    for k in range(17):
        t = math.radians(90 * k / 16)
        y = -(20 + R) + (R + d) * math.cos(t)
        if y < -15.5:
            pts.append((y, FOOT_H + R - (R + d) * math.sin(t)))
    pts += [(-76, 5 - d), (-76, 45)]
    # raised logo on the outer face
    logo = text_obj('logo', 'MuLab', 8.0, 1.6, M_BASE)
    logo.data.transform(Matrix.Translation((m(FX0), 0, m(19.0))) @ Matrix(((0, 0, -1, 0), (-1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    boolean(foot, logo, 'UNION')
    # vertical socket + M5 from below into the upright's axial bore
    boolean(foot, box('sock', cx - UP / 2 - 0.15, cx + UP / 2 + 0.15, -UP / 2 - 0.15, UP / 2 + 0.15, UP_Z0, FOOT_TOP + 5))
    boolean(foot, cyl('clr', cx, 0, 2.75, -1, UP_Z0 + 1, 40))
    boolean(foot, cyl('cbore', cx, 0, 4.75, -1, 5.0, 48))
    # side pocket for the horizontal profile (opens on the inner face)
    boolean(foot, box('hpock', -H_X - 0.2, FX1 + 2, -UP / 2 - 0.15, UP / 2 + 0.15, H_Z0 - 0.1, H_Z0 + UP + 0.2))
    # M5 button screw from below into a slot nut in the profile's bottom slot
    boolean(foot, cyl('bclr', BS_X, 0, 2.75, -1, H_Z0 + 1, 40))
    boolean(foot, cyl('bcb', BS_X, 0, 5.1, -1, 3.0, 48))
    # locating-pin holes for the board module (front and back, foot is reversible)
    for py in (-PIN_Y, PIN_Y):
        boolean(foot, cyl('pinh', PIN_X, py, 1.9, 2.0, FOOT_H + 2, 24))
    # rubber pad recesses
    for py in (-60.0, 60.0):
        boolean(foot, cyl('padrec', cx, py, 6.3, -1, 1.0, 48))
    setmat(foot, M_BASE)
    smooth(foot, 35)
    return foot


def rot180(ob, name):
    new = ob.copy()
    new.data = ob.data.copy()
    new.name = name
    scene.collection.objects.link(new)
    new.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))
    return new


def make_base():
    left = make_foot('foot_L')
    rot180(left, 'foot_R')
    hp = make_upright('hprofile', 0.0, -H_LEN / 2, H_LEN)
    hp.data.transform(Matrix.Translation((0, 0, m(H_Z0 + UP / 2))) @ Matrix.Rotation(math.pi / 2, 4, 'Y'))
    for cx in (UX, -UX):
        for py in (-60.0, 60.0):
            p = cyl('rubber', cx, py, 6.0, -2.0, 0.9, 48)
            bevel(p, 0.8, 2)
            setmat(p, M_RUBBER)
            smooth(p, 40)
    return left


def make_spacer(name, z0):
    z1 = z0 + 10.0
    sp = box(name, X_BACK, X_BOTTOM + 1.0, -13, 13, z0 + 0.05, z1 - 0.05)
    bevel(sp, 0.6, 2)
    neck = box('neck', X_BACK - 2.0, X_BACK + 0.2, -2.5, 2.5, z0 + 0.05, z1 - 0.05)
    head = box('head', X_BACK - 4.0, X_BACK - 1.95, -3.7, 3.7, z0 + 0.05, z1 - 0.05)
    boolean(sp, neck, 'UNION')
    boolean(sp, head, 'UNION')
    setmat(sp, M_SPACER)
    smooth(sp, 35)
    mirror_x(sp, name + 'R')
    return sp


k = 0
for a, b in [(SOCK_TOP, BAR_Z[0] - 10), (BAR_Z[0] + 10, BAR_Z[1] - 10), (BAR_Z[1] + 10, BAR_Z[2] - 10)]:
    z = a
    while z + 10 <= b + 1e-6:
        make_spacer(f'spacer{k}', z)
        z += 10.0
        k += 1


base = make_base()
upL = make_upright('upright_L', UX)
upR = make_upright('upright_R', -UX)
def engrave_number(ob, num, xc, zc):
    hw = BAR_W / 2 + CLR + WALL_YZ
    t = text_obj('num', str(num), 7.0, 1.2, M_CLIP)
    t.data.transform(Matrix.Translation((m(xc), m(-hw), m(zc))) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
    boolean(ob, t)


for i, zc in enumerate(BAR_Z):
    make_bar(f'bar{i}', zc)
    cl = make_clip(f'clipL{i}', zc)
    cr = mirror_x(cl, f'clipR{i}')
    engrave_number(cl, i + 1, (X_BACK + X_MOUTH) / 2, zc)
    engrave_number(cr, i + 1, -(X_BACK + X_MOUTH) / 2, zc)
    make_pcb(zc)


# ---------------------------------------------------------------- M5x16 socket head screws (from below)
def make_bolt(name, cx):
    head = cyl(name, cx, 0, 4.25, 0.0, 5.0, 48)
    bevel(head, 0.4, 2)
    hexs = [(cx + 2.06 * math.cos(math.pi / 3 * i), 2.06 * math.sin(math.pi / 3 * i)) for i in range(6)]
    boolean(head, prism('hex', hexs, -1, 3.0))
    shank = cyl('shank', cx, 0, 2.45, 4.9, 21.0, 32)
    bevel(shank, 0.4, 1)
    boolean(head, shank, 'UNION')
    setmat(head, M_BOLT)
    smooth(head, 40)
    # thread hint: thin dark rings
    rings = []
    for i in range(18):
        z = 6.0 + i * 0.8
        r = cyl('ring', cx, 0, 2.52, z, z + 0.28, 32)
        boolean(head, r, 'UNION')
    return head


BOLTS = [make_bolt('bolt_L', UX), make_bolt('bolt_R', -UX)]


def socket_screw(name, d, L, dk, k):
    """ISO 4762 screw in local frame: bearing face at z=0, head in +z, shank in -z."""
    h = cyl(name, 0, 0, dk / 2, 0, k, 48)
    bevel(h, 0.35, 2)
    s_ = 0.4 * dk
    hexs = [(s_ * math.cos(math.pi / 3 * i), s_ * math.sin(math.pi / 3 * i)) for i in range(6)]
    boolean(h, prism('hex', hexs, k * 0.4, k + 1))
    sh = cyl('sh', 0, 0, d / 2 - 0.05, -L, 0.1, 32)
    bevel(sh, 0.3, 1)
    boolean(h, sh, 'UNION')
    for i in range(int((L - 2) / 0.7)):
        z = -L + 1.0 + i * 0.7
        boolean(h, cyl('ring', 0, 0, d / 2 + 0.02, z, z + 0.25, 32), 'UNION')
    setmat(h, M_BOLT)
    smooth(h, 40)
    return h


def hex_nut(name, d, af, t):
    rr = af / math.sqrt(3)
    pts = [(rr * math.cos(math.pi / 3 * i + math.pi / 6), rr * math.sin(math.pi / 3 * i + math.pi / 6)) for i in range(6)]
    n = prism(name, pts, 0, t)
    bevel(n, 0.3, 1)
    boolean(n, cyl('nh', 0, 0, d / 2, -1, t + 1, 32))
    setmat(n, M_BOLT)
    smooth(n, 40)
    return n


def place(ob, mat):
    ob.data.transform(mat)
    ob.data.update()


def button_screw(name, d, L, dk, k):
    """ISO 7380 button head in local frame: bearing at z=0, head +z, shank -z."""
    h = cyl(name, 0, 0, dk / 2, 0, k, 48)
    bevel(h, 1.1, 4)
    s_ = 0.3 * dk
    hexs = [(s_ * math.cos(math.pi / 3 * i), s_ * math.sin(math.pi / 3 * i)) for i in range(6)]
    boolean(h, prism('hex', hexs, k * 0.35, k + 1))
    boolean(h, cyl('sh', 0, 0, d / 2 - 0.05, -L, 0.1, 32), 'UNION')
    for i in range(int((L - 2) / 0.8)):
        z = -L + 1.0 + i * 0.8
        boolean(h, cyl('ring', 0, 0, d / 2 + 0.02, z, z + 0.28, 32), 'UNION')
    setmat(h, M_BOLT)
    smooth(h, 40)
    return h


def slot_nut(name, x):
    """M5 slot nut sitting in the bottom slot of the horizontal profile."""
    n = box(name, x - 5.0, x + 5.0, -4.4, 4.4, H_Z0 + SL_LIP + 0.1, H_Z0 + SL_LIP + 3.1)
    bevel(n, 0.4, 1)
    boolean(n, box('neck', x - 5.0, x + 5.0, -2.7, 2.7, H_Z0 + 0.3, H_Z0 + SL_LIP + 0.3), 'UNION')
    boolean(n, cyl('nh', x, 0, 2.5, H_Z0 - 1, H_Z0 + 6, 32))
    setmat(n, M_BOLT)
    smooth(n, 40)
    return n


HW = []
for x in (BS_X, -BS_X):
    bs = button_screw('bscrew', 5.0, 8.0, 9.5, 2.75)
    place(bs, Matrix.Translation((m(x), 0, m(3.0))) @ Matrix.Rotation(math.pi, 4, 'X'))
    HW.append((x, bs, slot_nut('tnut', x)))


# ---------------------------------------------------------------- end caps
def make_cap(name, cx):
    zt = UP_Z0 + UP_H
    cap = box(name, cx - UP / 2, cx + UP / 2, -UP / 2, UP / 2, zt, zt + 3.0)
    bevel(cap, 0.9, 3)
    plug = cyl('plug', cx, 0, 2.05, zt - 7.0, zt + 0.5, 32)
    boolean(cap, plug, 'UNION')
    # four small snap tabs entering the slots
    for k in range(4):
        a = k * math.pi / 2
        nx, ny = math.cos(a), math.sin(a)
        r = UP / 2 - 1.0
        px, py = cx + nx * r, ny * r
        hw = 2.6
        radial_x = abs(nx) > 0.5
        tab = box('tab', px - (0.9 if radial_x else hw), px + (0.9 if radial_x else hw), py - (hw if radial_x else 0.9), py + (hw if radial_x else 0.9), zt - 5.0, zt + 0.5)
        boolean(cap, tab, 'UNION')
    setmat(cap, M_CAP_TOP)
    smooth(cap, 35)
    return cap


CAPS = [make_cap('cap_L', UX), make_cap('cap_R', -UX)]


# ---------------------------------------------------------------- 3-channel readout board (glacier-elettronica, variante_3ch)
import json, os
BOARD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scheda3ch')
BRD = json.load(open(os.path.join(BOARD_DIR, 'scene.json')))
BX1, BY1, BX2, BY2 = BRD['board']
BW_, BH_ = BX2 - BX1, BY2 - BY1                 # 103 x 215
B_T = BRD['thickness']
SUP_TOP = H_Z0 + UP                            # top of the module rails = top of the cross-member (26)
STANDOFF = 8.0
B_BOT = SUP_TOP + 2.0 + STANDOFF                # underside of the PCB (bosses 2 mm)
B_TOPZ = B_BOT + B_T                            # component side (faces +z)
B_YBACK = -34.0                                 # PCB edge with the KK inputs (toward the bars)
RAIL_Y0, RAIL_Y1 = -142.0, -10.3                # rails: from the front to the cross-member face


def board_world():
    """board-local mm (X along width, Y = -(y - Y1), Z up from the top copper) -> world metres.
    Lying flat on the base under the bars, components up: the 215 mm side runs along the frame
    (power + channel 1 on the left, coincidence on the right), KK inputs on the front edge,
    LEMO outputs on the back edge."""
    R = Matrix(((0, 1, 0, 0), (-1, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
    return Matrix.Diagonal((MM, MM, MM, 1.0)) @ Matrix.Translation((BH_ / 2, B_YBACK, B_TOPZ)) @ R


C3 = Matrix(((1, 0, 0, -BX1), (0, 0, -1, BY1), (0, 1, 0, 0), (0, 0, 0, 1)))   # three.js (x,y,z) -> board-local
BWM = board_world() @ C3


def pmat(name, rgb, rough, metal=0.0, trans=0.0):
    mt = mat_simple(name, rgb, rough, metal)
    if trans:
        mt.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value = trans
    return mt


BM_MATS = {
    'epoxy': pmat('b_epoxy', (0.017, 0.017, 0.019), 0.45), 'tin': pmat('b_tin', (0.62, 0.63, 0.65), 0.3, 0.9),
    'gold': pmat('b_gold', (0.69, 0.43, 0.07), 0.3, 0.9), 'chrome': pmat('b_chrome', (0.74, 0.77, 0.79), 0.18, 1.0),
    'brass': pmat('b_brass', (0.58, 0.36, 0.07), 0.35, 0.9), 'ceramic': pmat('b_cer', (0.45, 0.33, 0.17), 0.7),
    'ceramicHV': pmat('b_cerhv', (0.32, 0.23, 0.13), 0.7), 'white': pmat('b_white', (0.87, 0.87, 0.87), 0.5),
    'blue': pmat('b_trim', (0.025, 0.1, 0.48), 0.45), 'redLed': pmat('b_led', (1.0, 0.03, 0.03), 0.15, 0, 0.4),
    'plastic': pmat('b_plastic', (0.008, 0.008, 0.008), 0.7), 'resTop': pmat('b_res', (0.005, 0.005, 0.005), 0.5),
    'redTP': pmat('b_redtp', (0.52, 0.02, 0.025), 0.5), 'blackTP': pmat('b_blktp', (0.016, 0.016, 0.016), 0.5),
    'inductor': pmat('b_ind', (0.023, 0.023, 0.023), 0.75), 'ferrite': pmat('b_fer', (0.07, 0.07, 0.07), 0.8),
    'glass': pmat('b_glass', (0.7, 0.28, 0.12), 0.1, 0, 0.6), 'dark': pmat('b_dark', (0.01, 0.01, 0.01), 0.7),
    'nylon': M_NYLON,
}
BM = {k: bmesh.new() for k in BM_MATS}


def comp_matrix(c):
    return BWM @ Matrix.Translation((c['x'], 0, c['y'])) @ Matrix.Rotation(c['rot'], 4, 'Y')


def pbox(Mc, w, h, d, mk, x, y, z):
    bmesh.ops.create_cube(BM[mk], size=1.0, matrix=Mc @ Matrix.Translation((x, y, z)) @ Matrix.Diagonal((w, h, d, 1)))


def pcyl(Mc, r, ln, mk, axis, x, y, z, seg=24):
    rot = {'y': Matrix.Rotation(-math.pi / 2, 4, 'X'), 'x': Matrix.Rotation(math.pi / 2, 4, 'Y'), 'z': Matrix.Identity(4)}[axis]
    bmesh.ops.create_cone(BM[mk], cap_ends=True, segments=seg, radius1=r, radius2=r, depth=ln,
                          matrix=Mc @ Matrix.Translation((x, y, z)) @ rot)


def ptorus(Mc, R, r, mk, x, y, z, nu=24, nv=10):
    bm = BM[mk]
    Mt = Mc @ Matrix.Translation((x, y, z))
    rings = []
    for i in range(nu):
        a = 2 * math.pi * i / nu
        ring = []
        for j in range(nv):
            b = 2 * math.pi * j / nv
            p = Vector(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
            ring.append(bm.verts.new(Mt @ p))
        rings.append(ring)
    for i in range(nu):
        for j in range(nv):
            i2, j2 = (i + 1) % nu, (j + 1) % nv
            bm.faces.new([rings[i][j], rings[i2][j], rings[i2][j2], rings[i][j2]])


def gull(Mc, x0, x1, z, H):
    t, wd = 0.15, 0.42
    mid = (x0 + x1) / 2
    pbox(Mc, abs(mid - x0) + 0.1, t, wd, 'tin', (x0 + mid) / 2, H * 0.45, z)
    pbox(Mc, t, H * 0.45, wd, 'tin', mid, H * 0.225, z)
    pbox(Mc, abs(x1 - mid) + 0.1, t, wd, 'tin', (mid + x1) / 2, t / 2, z)


def cap_(Mc, L, Wd, H, mk):
    pbox(Mc, L - 0.7, H, Wd, mk, 0, H / 2, 0)
    for s in (-1, 1):
        pbox(Mc, 0.4, H + 0.02, Wd + 0.02, 'tin', s * (L / 2 - 0.2), H / 2, 0)


def sot_(Mc, L, Wd, H, pins):
    pbox(Mc, L, H, Wd, 'epoxy', 0, H / 2 + 0.1, 0)
    for x, s in pins:
        pbox(Mc, 0.4, 0.15, 0.55, 'tin', x, 0.08, s * (Wd / 2 + 0.35))
        pbox(Mc, 0.4, H * 0.45, 0.15, 'tin', x, H * 0.25, s * (Wd / 2 + 0.05))


KK_IN = {}      # ref -> world point (m) where the cable enters the plugged KK housing


def build_component(c):
    Mc = comp_matrix(c)
    fp = c['fp']
    if fp == 'R_0805':
        pbox(Mc, 1.4, 0.45, 1.25, 'resTop', 0, 0.25, 0)
        for s in (-1, 1):
            pbox(Mc, 0.35, 0.5, 1.27, 'tin', s * 0.85, 0.25, 0)
    elif fp == 'C_0805':
        cap_(Mc, 2.0, 1.25, 0.9, 'ceramic')
    elif fp == 'C_1206':
        cap_(Mc, 3.2, 1.6, 1.1, 'ceramicHV')
    elif fp == 'C_1210':
        cap_(Mc, 3.2, 2.5, 1.6, 'ceramicHV')
    elif fp == 'LED_0805':
        pbox(Mc, 2.0, 0.35, 1.25, 'white', 0, 0.17, 0)
        pbox(Mc, 1.4, 0.45, 1.1, 'redLed', 0, 0.55, 0)
        for s in (-1, 1):
            pbox(Mc, 0.35, 0.36, 1.27, 'tin', s * 0.85, 0.17, 0)
    elif fp == 'SOT23':
        sot_(Mc, 2.9, 1.3, 1.0, [(-0.95, 1), (0.95, 1), (0, -1)])
    elif fp == 'SOT23-5':
        sot_(Mc, 2.9, 1.6, 1.1, [(-0.95, 1), (0, 1), (0.95, 1), (0.95, -1), (-0.95, -1)])
    elif fp == 'SOT23-6':
        sot_(Mc, 2.9, 1.6, 1.0, [(-0.95, 1), (0, 1), (0.95, 1), (0.95, -1), (0, -1), (-0.95, -1)])
    elif fp in ('SOIC8', 'SOIC14'):
        n = 4 if fp == 'SOIC8' else 7
        pbox(Mc, 3.9, 1.5, 4.9 if n == 4 else 8.65, 'epoxy', 0, 0.85, 0)
        for i in range(n):
            z = -(n - 1) * 1.27 / 2 + i * 1.27
            gull(Mc, 1.95, 3.1, z, 1.5)
            gull(Mc, -1.95, -3.1, z, 1.5)
    elif fp == 'SOT223':
        pbox(Mc, 6.5, 1.6, 3.5, 'epoxy', 0, 0.9, 0)
        for x in (-2.3, 0, 2.3):
            pbox(Mc, 0.7, 0.15, 1.6, 'tin', x, 0.4, 2.4)
            pbox(Mc, 0.7, 0.15, 1.2, 'tin', x, 0.08, 3.1)
        pbox(Mc, 3.0, 0.2, 1.6, 'tin', 0, 0.1, -2.6)
    elif fp == 'L_PWR_5050':
        pbox(Mc, 5, 4, 5, 'inductor', 0, 2, 0)
        pcyl(Mc, 1.8, 0.05, 'ferrite', 'y', 0, 4.02, 0)
    elif fp == 'D_DO35':
        y = 1.3
        pcyl(Mc, 0.85, 3.8, 'glass', 'x', 0, y, 0)
        pcyl(Mc, 0.87, 0.5, 'dark', 'x', -1.4, y, 0)
        for s in (-1, 1):
            pcyl(Mc, 0.25, 1.9, 'tin', 'x', s * 2.85, y, 0, 10)
            pcyl(Mc, 0.25, y, 'tin', 'y', s * 3.81, y / 2, 0, 10)
    elif fp == 'TRIM_3296W':
        pbox(Mc, 9.5, 10, 4.8, 'blue', 0, 5.2, 0)
        pcyl(Mc, 1.15, 1.2, 'brass', 'y', 3.4, 10.6, 0)
        pbox(Mc, 1.8, 0.25, 0.35, 'dark', 3.4, 11.25, 0)
    elif fp in ('HDR1x02', 'HDR1x03'):
        n = 2 if fp == 'HDR1x02' else 3
        pbox(Mc, 2.54 * n, 2.5, 2.54, 'plastic', 1.27 * (n - 1), 1.25, 0)
        for k in range(n):
            pbox(Mc, 0.64, 8.5, 0.64, 'gold', 2.54 * k, 3.25, 0)
        if c['ref'] == 'J3':                      # 5 V supply: 2-way housing plugged on the pins
            pbox(Mc, 5.1, 14.0, 2.6, 'plastic', 1.27, 2.6 + 7.0, 0)
            KK_IN['J3'] = Mc @ Vector((1.27, 16.6, 0))
    elif fp == 'MOLEX_KK_2':
        pbox(Mc, 6.1, 3.2, 5.6, 'nylon', 1.27, 1.6, 0)
        pbox(Mc, 6.1, 2.6, 0.9, 'nylon', 1.27, 4.5, 2.35)
        pbox(Mc, 1.4, 0.8, 0.5, 'nylon', 1.27, 3.6, 1.7)
        for x in (0, 2.54):
            pbox(Mc, 0.64, 9.0, 0.64, 'gold', x, 3.6, 0)
        # crimp housing 22-01-3027 plugged from above, cable leaves on top
        pbox(Mc, 5.0, 12.4, 4.6, 'nylon', 1.27, 3.25 + 6.2, -0.45)
        pbox(Mc, 1.6, 1.0, 0.8, 'nylon', 1.27, 6.0, 1.85)         # latch over the ramp
        KK_IN[c['ref']] = Mc @ Vector((1.27, 15.6, -0.45))
    elif fp == 'LEMO_EPL00':
        pbox(Mc, 7, 7, 7, 'chrome', 0, 3.6, 0)
        pcyl(Mc, 2.9, 10.5, 'chrome', 'x', 8.6, 3.6, 0, 40)
        pcyl(Mc, 3.2, 1.2, 'chrome', 'x', 4.5, 3.6, 0, 40)
        pcyl(Mc, 1.4, 0.3, 'dark', 'x', 13.9, 3.6, 0, 32)
        pcyl(Mc, 0.35, 0.4, 'gold', 'x', 14.0, 3.6, 0, 16)
    elif fp == 'TP_THT':
        mk = 'blackTP' if c['value'] == 'GND' else 'redTP'
        ptorus(Mc, 1.2, 0.22, mk, 0, 3.2, 0)
        for s in (-1, 1):
            pcyl(Mc, 0.22, 2.2, mk, 'y', s * 1.0, 1.1, 0, 8)


def build_board():
    objs = []
    # PCB with the real top texture (black solder mask variant)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=BWM @ Matrix.Translation(((BX1 + BX2) / 2, -B_T / 2, (BY1 + BY2) / 2))
                          @ Matrix.Diagonal((BW_, B_T, BH_, 1)))
    uv = bm.loops.layers.uv.new()
    Minv = BWM.inverted()
    for f in bm.faces:
        cen = Minv @ f.calc_center_median()
        if cen.y > -0.01:                      # top face (three y = 0)
            f.material_index = 1
            for lp in f.loops:
                p = Minv @ lp.vert.co
                lp[uv].uv = ((p.x - BX1) / BW_, 1.0 - (p.z - BY1) / BH_)
    pcb = mesh_obj('board3ch', bm)
    side = mat_simple('b_side', (0.012, 0.012, 0.012), 0.6)
    top = bpy.data.materials.new('b_top')
    top.use_nodes = True
    nt = top.node_tree
    bs = nt.nodes['Principled BSDF']
    bs.inputs['Roughness'].default_value = 0.4
    bs.inputs['Coat Weight'].default_value = 0.25
    img = nt.nodes.new('ShaderNodeTexImage')
    img.image = bpy.data.images.load(os.path.join(BOARD_DIR, 'top_nero.png'))
    img.interpolation = 'Cubic'
    nt.links.new(img.outputs['Color'], bs.inputs['Base Color'])
    pcb.data.materials.append(side)
    pcb.data.materials.append(top)
    objs.append(pcb)
    for c in BRD['comps']:
        build_component(c)
    for k, bmk in BM.items():
        if len(bmk.verts):
            o = mesh_obj('bcomp_' + k, bmk)
            setmat(o, BM_MATS[k])
            objs.append(o)
    return objs


BOARD_OBJS = build_board()
MH_WORLD = [BWM @ Vector((c['x'], 0, c['y'])) for c in BRD['comps'] if c['fp'] == 'MH_M3']


# ---- removable board module: 3 printed rails + standoffs + board, held by 3 thumb screws
M_KNURL = mat_simple('knurl', (0.02, 0.02, 0.022), 0.45)
HOLE_X = sorted({round(p.x / MM, 2) for p in MH_WORLD})          # 4 columns of board holes
HOLE_Y = sorted({round(p.y / MM, 2) for p in MH_WORLD})          # 2 rows
MODULE = []


def rail_common(ob, x0, x1, lip_x0, lip_x1):
    # lip resting on top of the cross-member
    lip = box('lip', lip_x0, lip_x1, RAIL_Y1 - 0.5, 4.0, SUP_TOP, SUP_TOP + 4.0)
    bevel(lip, 1.0, 2)
    boolean(ob, lip, 'UNION')


def thumb_screw(x):
    """M5 knurled thumb screw, horizontal, into a slot nut in the front slot of the cross-member."""
    zc = H_Z0 + UP / 2
    head = prism('thumb', [(x + 6.0 * math.cos(2 * math.pi * k / 30) * (1 if k % 2 else 0.93),
                            zc + 6.0 * math.sin(2 * math.pi * k / 30) * (1 if k % 2 else 0.93)) for k in range(30)],
                 -27.0, -20.5, axis='y') if False else None
    pts = []
    for k in range(48):
        a = 2 * math.pi * k / 48
        r = 6.0 if k % 2 == 0 else 5.6
        pts.append((x + r * math.cos(a), zc + r * math.sin(a)))
    bm = bmesh.new()
    vb = [bm.verts.new((m(px), m(-27.0), m(pz))) for px, pz in pts]
    vt = [bm.verts.new((m(px), m(-21.0), m(pz))) for px, pz in pts]
    bm.faces.new(vb); bm.faces.new(list(reversed(vt)))
    for i in range(48):
        j = (i + 1) % 48
        bm.faces.new([vb[i], vb[j], vt[j], vt[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    t = mesh_obj('thumb', bm)
    boolean(t, cyl('sh', x, zc, 2.45, -21.2, -5.0, 32, axis='y'), 'UNION')
    setmat(t, M_KNURL)
    smooth(t, 20)
    return t


def make_side_rail(name):
    x0, x1 = UX + 30.2, HOLE_X[0] + 7.5          # from the foot's inner face to past the board holes
    r = box(name, x0, x1, RAIL_Y0, RAIL_Y1, 0, SUP_TOP)
    bevel(r, 2.0, 3)
    rail_common(r, x0, x1, x0 + 4, x1 - 4)
    # tab over the foot plate, onto the locating pin
    tab = box('tab', UX + 9.5, x0 + 1, -PIN_Y - 7.5, -PIN_Y + 7.5, 10.5, 15.0)
    bevel(tab, 1.5, 2)
    boolean(r, tab, 'UNION')
    boolean(r, cyl('tabh', PIN_X, -PIN_Y, 2.2, 8, 17, 24))
    # lightening window and thumb-screw pocket (open on top, behind the board edge)
    boolean(r, box('win', x0 - 1, x1 + 1, -100, -50, 6, 20))
    xs = (x0 + x1) / 2
    boolean(r, box('pock', xs - 7.5, xs + 7.5, -31, -17, 5, SUP_TOP + 5))
    boolean(r, cyl('sh', xs, H_Z0 + UP / 2, 2.75, -18, -9, 32, axis='y'))
    for y in HOLE_Y:
        boolean(r, cyl('boss', HOLE_X[0], y, 4.6, SUP_TOP - 0.5, SUP_TOP + 2.0, 40), 'UNION')
        boolean(r, cyl('bh', HOLE_X[0], y, 1.6, SUP_TOP - 8, SUP_TOP + 3, 24))
    setmat(r, M_BASE)
    smooth(r, 35)
    return r, xs


def make_center_rail(name):
    xa, xb = HOLE_X[1], HOLE_X[2]
    r = box(name, xa - 6, xb + 6, RAIL_Y1 - 16, RAIL_Y1, 0, SUP_TOP)          # back cross piece
    for xc in (xa, xb):
        rib = box('rib', xc - 6, xc + 6, RAIL_Y0, RAIL_Y1, 0, SUP_TOP)
        bevel(rib, 2.0, 3)
        boolean(rib, box('win', xc - 7, xc + 7, -100, -50, 6, 20))
        boolean(r, rib, 'UNION')
    front = box('front', xa - 6, xb + 6, RAIL_Y0, RAIL_Y0 + 10, 0, 10)
    bevel(front, 1.5, 2)
    boolean(r, front, 'UNION')
    rail_common(r, xa - 6, xb + 6, xa - 2, xb + 2)
    xs = (xa + xb) / 2
    boolean(r, box('pock', xs - 7.5, xs + 7.5, -31, -17, 5, SUP_TOP + 5))
    boolean(r, cyl('sh', xs, H_Z0 + UP / 2, 2.75, -18, -9, 32, axis='y'))
    for xc in (xa, xb):
        for y in HOLE_Y:
            boolean(r, cyl('boss', xc, y, 4.6, SUP_TOP - 0.5, SUP_TOP + 2.0, 40), 'UNION')
            boolean(r, cyl('bh', xc, y, 1.6, SUP_TOP - 8, SUP_TOP + 3, 24))
    setmat(r, M_BASE)
    smooth(r, 35)
    return r, xs


railL, xsL = make_side_rail('bsupL')
railR = mirror_x(railL, 'bsupR')
railC, xsC = make_center_rail('bsupC')
MODULE += [railL, railR, railC]
for x in (xsL, -xsL, xsC):
    MODULE.append(thumb_screw(x))
for x in (xsL, -xsL, HOLE_X[1], HOLE_X[2]):
    for y in (RAIL_Y1 - 16, RAIL_Y0 + 12):
        p = cyl('bpad', x, y, 5.0, -2.0, 0.9, 40)
        bevel(p, 0.8, 2)
        setmat(p, M_RUBBER)
        MODULE.append(p)
# locating pins in the feet (front holes)
for sx in (1, -1):
    pn = cyl('fpin', sx * PIN_X, -PIN_Y, 1.9, 3.0, 17.5, 24)
    bevel(pn, 0.6, 2)
    setmat(pn, M_BOLT)

M_STANDOFF = mat_simple('standoff', (0.015, 0.015, 0.016), 0.55)
BOARD_HW = []
ARMS = []
for k, p in enumerate(MH_WORLD):
    x, y = p.x / MM, p.y / MM
    so = prism(f'standoff{k}', [(x + 3.17 * math.cos(math.pi / 3 * i), y + 3.17 * math.sin(math.pi / 3 * i)) for i in range(6)],
               SUP_TOP + 2.0, B_BOT)
    bevel(so, 0.3, 1)
    setmat(so, M_STANDOFF)
    BOARD_HW.append(so)
    sc = cyl(f'm3head{k}', x, y, 2.75, B_TOPZ, B_TOPZ + 2.0, 32)
    bevel(sc, 0.7, 3)
    boolean(sc, prism('rec', [(x + 1.2 * math.cos(math.pi / 3 * i), y + 1.2 * math.sin(math.pi / 3 * i)) for i in range(6)],
                      B_TOPZ + 1.0, B_TOPZ + 3))
    setmat(sc, M_BOLT)
    BOARD_HW.append(sc)
MODULE += BOARD_HW + BOARD_OBJS

# ---------------------------------------------------------------- compute module: Raspberry Pi Zero 2 W in a fan-cooled printed box
# on the outer face of the right upright (far from the SiPMs), removable: 2 ears with T keys + thumb screws
M_PIGRN = mat_simple('pi_pcb', (0.02, 0.17, 0.05), 0.35, coat=0.3)
M_FAN = mat_simple('fan', (0.015, 0.015, 0.016), 0.5)
CB_X0, CB_X1 = -UX + UP / 2, -UX + UP / 2 + 26.0        # 174 .. 200 (back on the upright, lid face)
CB_Y0, CB_Y1 = -25.0, 25.0
CB_Z0, CB_Z1 = 98.0, 202.0
CB_W = 2.5                                              # wall
LID_T = 2.5
PI_X = CB_X0 + 3.0 + 8.0                                # back face of the Pi PCB (bosses 8 mm)
PI_Y0 = CB_Y0 + CB_W + 1.0                              # Pi edge with the ports (front)
PI_Z0 = CB_Z0 + CB_W + 2.0                              # Pi end with the microSD (bottom)
PI_T = 1.0
PZ = lambda u: PI_Z0 + u                                # Pi long axis (65 mm) -> world z
PY = lambda v: PI_Y0 + v                                # Pi short axis (30 mm) -> world y
PT = PI_X + PI_T                                        # top copper of the Pi (x)
FAN_Z0 = PZ(65) + 2.0
COMPUTE = []                                            # parts of the compute module
LID_PARTS = []


def ear(z0, z1):
    e = box('ear', CB_X0, CB_X0 + 6, -11, 11, z0, z1)
    bevel(e, 1.5, 2)
    f = CB_X0
    boolean(e, box('neck', f - 2.0, f + 0.2, -2.5, 2.5, z0 + 1, z1 - 1), 'UNION')
    boolean(e, box('head', f - 4.0, f - 1.95, -3.7, 3.7, z0 + 1, z1 - 1), 'UNION')
    zc = (z0 + z1) / 2
    boolean(e, prism('eh', [(2.75 * math.cos(2 * math.pi * k / 32), zc + 2.75 * math.sin(2 * math.pi * k / 32)) for k in range(32)], f - 5, f + 7, axis='x'))
    return e


def knurled_x(name, y, z, x0, x1, r=6.0):
    pts = [(y + (r if k % 2 == 0 else r - 0.4) * math.cos(2 * math.pi * k / 48), z + (r if k % 2 == 0 else r - 0.4) * math.sin(2 * math.pi * k / 48)) for k in range(48)]
    t = prism(name, pts, x0, x1, axis='x')
    bevel(t, 0.5, 2, angle=60)
    boolean(t, prism('sh', [(y + 2.45 * math.cos(2 * math.pi * k / 24), z + 2.45 * math.sin(2 * math.pi * k / 24)) for k in range(24)], CB_X0 - 6, x0 + 0.1, axis='x'), 'UNION')
    setmat(t, M_KNURL)
    smooth(t, 20)
    return t


def make_compute_base():
    b = box('cbox', CB_X0, CB_X1 - LID_T, CB_Y0, CB_Y1, CB_Z0, CB_Z1)
    bevel(b, 2.5, 3)
    boolean(b, box('cav', CB_X0 + 3.0, CB_X1, CB_Y0 + CB_W, CB_Y1 - CB_W, CB_Z0 + CB_W, CB_Z1 - CB_W))
    for z0, z1 in ((CB_Z0 - 12, CB_Z0 + 2), (CB_Z1 - 2, CB_Z1 + 12)):
        boolean(b, ear(z0, z1), 'UNION')
    # Pi bosses (M2.5) at the 4 mounting holes
    for u in (3.5, 61.5):
        for v in (3.5, 26.5):
            boolean(b, prism('boss', [(PY(v) + 3.0 * math.cos(2 * math.pi * k / 32), PZ(u) + 3.0 * math.sin(2 * math.pi * k / 32)) for k in range(32)],
                             CB_X0 + 1.0, PI_X, axis='x'), 'UNION')
    # port openings in the front wall: mini-HDMI, USB, PWR
    for u, w in ((12.4, 14.0), (41.4, 11.0), (54.0, 11.0)):
        boolean(b, box('port', PT - 2.0, PT + 6.5, CB_Y0 - 1, CB_Y0 + CB_W + 1, PZ(u) - w / 2, PZ(u) + w / 2))
    # microSD slot in the bottom wall
    boolean(b, box('sd', PT - 1.5, PT + 3.5, PY(16.9) - 7.5, PY(16.9) + 7.5, CB_Z0 - 1, CB_Z0 + CB_W + 1))
    # air intake: slots in the back (+y) wall
    for k in range(7):
        z = PZ(8) + k * 8.0
        boolean(b, box('vent', CB_X0 + 6, CB_X1 - 6, CB_Y1 - CB_W - 1, CB_Y1 + 1, z - 1.6, z + 1.6))
    setmat(b, M_BASE)
    smooth(b, 35)
    return b


def make_compute_lid():
    l = box('clid', CB_X1 - LID_T, CB_X1, CB_Y0, CB_Y1, CB_Z0, CB_Z1)
    bevel(l, 1.2, 3)
    # GPIO window: the whole 2x20 header is reachable from outside
    boolean(l, box('gw', CB_X1 - LID_T - 1, CB_X1 + 1, PY(26.5) - 4.5, PY(26.5) + 4.5, PZ(32.5) - 28, PZ(32.5) + 28))
    # fan grille (hex pattern of holes inside the fan circle)
    fy, fz = 0.0, FAN_Z0 + 15.0
    for i in range(-5, 6):
        for j in range(-5, 6):
            y = fy + 2.6 * i + (1.3 if j % 2 else 0.0)
            z = fz + 2.25 * j
            if (y - fy) ** 2 + (z - fz) ** 2 < 12.5 ** 2 and (y - fy) ** 2 + (z - fz) ** 2 > 4.5 ** 2:
                boolean(l, prism('gh', [(y + 0.95 * math.cos(math.pi / 3 * k + math.pi / 6), z + 0.95 * math.sin(math.pi / 3 * k + math.pi / 6)) for k in range(6)],
                                 CB_X1 - LID_T - 1, CB_X1 + 1, axis='x'))
    # engraved name
    t = text_obj('ltxt', 'MuLab', 6.0, 1.2, M_BASE)
    t.data.transform(Matrix.Translation((m(CB_X1), m(-11.0), m(PZ(32.5)))) @ Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    boolean(l, t)
    setmat(l, M_BASE)
    smooth(l, 35)
    return l


cbase = make_compute_base()
clid = make_compute_lid()
COMPUTE += [cbase, clid]
LID_PARTS.append(clid)
for zc in ((CB_Z0 - 12 + CB_Z0 + 2) / 2, (CB_Z1 - 2 + CB_Z1 + 12) / 2):
    COMPUTE.append(knurled_x('cthumb', 0.0, zc, CB_X0 + 6.0, CB_X0 + 12.0))

# Raspberry Pi Zero 2 W
BM = {k: bmesh.new() for k in BM_MATS}
BM_MATS['pigreen'] = M_PIGRN
BM_MATS['fan'] = M_FAN
BM = {k: bmesh.new() for k in BM_MATS}
I4 = Matrix.Diagonal((MM, MM, MM, 1.0))


def wb(mk, x0, x1, y0, y1, z0, z1):
    bmesh.ops.create_cube(BM[mk], size=1.0, matrix=I4 @ Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)))


wb('pigreen', PI_X, PT, PY(0), PY(30), PZ(0), PZ(65))
wb('epoxy', PT, PT + 1.2, PY(10), PY(22), PZ(27), PZ(39))                 # RP3A0 SiP
wb('chrome', PT, PT + 1.0, PY(8), PY(16), PZ(43), PZ(53))                  # RF shield
wb('chrome', PT, PT + 3.2, PY(-0.8), PY(6.7), PZ(12.4 - 5.6), PZ(12.4 + 5.6))   # mini HDMI
for u in (41.4, 54.0):
    wb('chrome', PT, PT + 2.8, PY(-1.0), PY(4.6), PZ(u - 4), PZ(u + 4))      # micro USB
wb('chrome', PT, PT + 1.4, PY(16.9 - 6), PY(16.9 + 6), PZ(0), PZ(11.5))      # microSD socket
wb('epoxy', PT + 0.2, PT + 1.0, PY(16.9 - 5.5), PY(16.9 + 5.5), PZ(-2.0), PZ(4))   # card
wb('epoxy', PT, PT + 1.2, PY(6.5), PY(23.5), PZ(61), PZ(65))               # CSI connector
wb('plastic', PT, PT + 2.5, PY(26.5) - 2.54, PY(26.5) + 2.54, PZ(32.5) - 25.4, PZ(32.5) + 25.4)   # 2x20 header
PIN = {}
for n in range(40):
    col, row = n // 2, n % 2
    z = PZ(32.5) - 24.13 + 2.54 * col
    y = PY(26.5) + (-1.27 if row == 0 else 1.27)
    PIN[n + 1] = (y, z)
    wb('gold', PT - 2.5, PT + 8.5, y - 0.32, y + 0.32, z - 0.32, z + 0.32)
for u in (3.5, 61.5):
    for v in (3.5, 26.5):
        bmesh.ops.create_cone(BM['tin'], cap_ends=True, segments=24, radius1=2.3, radius2=2.3, depth=1.8,
                              matrix=I4 @ Matrix.Translation((PT + 0.9, PY(v), PZ(u))) @ Matrix.Rotation(math.pi / 2, 4, 'Y'))
# 30 mm fan, mounted under the lid
wb('fan', CB_X1 - LID_T - 10.0, CB_X1 - LID_T, -15, 15, FAN_Z0, FAN_Z0 + 30)
for k in range(7):
    a = 2 * math.pi * k / 7
    bmesh.ops.create_cube(BM['dark'], size=1.0, matrix=I4 @ Matrix.Translation((CB_X1 - LID_T - 1.2, 7.0 * math.cos(a), FAN_Z0 + 15 + 7.0 * math.sin(a)))
                          @ Matrix.Rotation(a, 4, 'X') @ Matrix.Rotation(0.5, 4, 'Z') @ Matrix.Diagonal((1.2, 9.0, 4.0, 1)))
bmesh.ops.create_cone(BM['dark'], cap_ends=True, segments=32, radius1=4.0, radius2=4.0, depth=1.0,
                      matrix=I4 @ Matrix.Translation((CB_X1 - LID_T - 0.7, 0, FAN_Z0 + 15)) @ Matrix.Rotation(math.pi / 2, 4, 'Y'))
FAN_OBJS = []
for k, bmk in BM.items():
    if len(bmk.verts):
        o = mesh_obj('pi_' + k, bmk)
        setmat(o, BM_MATS[k])
        COMPUTE.append(o)
for o in COMPUTE:
    if o.name.startswith('pi_fan') or o.name.startswith('pi_dark'):
        LID_PARTS.append(o)

# GPIO harness head: 2x8 IDC housing on pins 1-16 + printed strain-relief hood; pins 17-40 stay free
HZ0, HZ1 = PIN[1][1] - 1.6, PIN[16][1] + 1.6
idc = box('idc', PT + 2.6, PT + 11.0, PY(26.5) - 2.9, PY(26.5) + 2.9, HZ0, HZ1)
bevel(idc, 0.3, 1)
setmat(idc, BM_MATS['plastic'])
hood = box('hood', PT + 10.5, CB_X1 + 9.0, PY(26.5) - 4.0, PY(26.5) + 4.0, HZ0 - 0.5, HZ1 + 0.5)
bevel(hood, 1.5, 3)
setmat(hood, M_CLIP)
smooth(hood, 35)
HARNESS = [idc, hood]
HOOD_TOP = CB_X1 + 9.0


# ---------------------------------------------------------------- cable clips (front slot, left upright)
W_R = 0.8                    # wire radius
W_Y = -(20 + FIL_R) + (FIL_R + CH_D - W_R)    # wire run y: tangent to the foot channel
W_X = [-5.0, -3.0, -1.0, 1.0, 3.0, 5.0]       # x offsets from the upright axis (top pair outermost)


COAX_R = 1.4                 # RG174
CX_Y = -16.3                 # coax axis y where it crosses the front of the left upright


def make_cable_clip(name, zc):
    x = UX
    f = -UP / 2
    c = box(name, x - 4.0, x + 4.0, CX_Y - 3.2, f + 0.1, zc - 3.6, zc + 3.6)
    bevel(c, 0.8, 2)
    boolean(c, prism('ch', [(CX_Y + (COAX_R + 0.1) * math.cos(2 * math.pi * k / 32), zc + (COAX_R + 0.1) * math.sin(2 * math.pi * k / 32)) for k in range(32)],
                     x - 6, x + 6, axis='x'))
    boolean(c, box('slit', x - 6, x + 6, CX_Y - 5, CX_Y, zc - 1.0, zc + 1.0))
    boolean(c, box('neck', x - 2.5, x + 2.5, f - 0.2, f + 2.0, zc - 3.6, zc + 3.6), 'UNION')
    boolean(c, box('head', x - 3.7, x + 3.7, f + 1.95, f + 4.0, zc - 3.6, zc + 3.6), 'UNION')
    setmat(c, M_BASE)
    smooth(c, 35)
    return c


CLIP_Z = []
CCLIPS = [make_cable_clip(f'cclip{k}', z) for k, z in enumerate(CLIP_Z)]

# ---------------------------------------------------------------- cables
def wire(name, pts, mat, r=0.8):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = m(r)
    cu.bevel_resolution = 4
    cu.resolution_u = 24
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = (m(p[0]), m(p[1]), m(p[2]))
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
    # straight entry into the terminal
    b0 = sp.bezier_points[0]
    b0.handle_left_type = b0.handle_right_type = 'VECTOR'
    ob = bpy.data.objects.new(name, cu)
    scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


CABLES = []
if not EXPLODED:
    for i, zc in enumerate(BAR_Z):
        ents = [e for e in ENTRIES if e[3] == zc]
        hx = sum(e[0] for e in ents) / len(ents)
        hs0, ze = ents[0][1], ents[0][2]
        E = KK_IN[f'J{i + 1}01'] / MM
        zr = E.z + 18.0 + 6.0 * i
        pts = [(hx, hs0 + 3.0, ze), (hx, hs0 - 4.0, ze), (hx - 2, hs0 - 10.0, ze - 4)]
        if i > 0:
            xv, yv = hx - 5.0 - 4.0 * i, -45.0 - 2.0 * i
            pts += [(xv, yv, ze - 18), (xv, yv, zr + 10)]
        pts += [((hx + E.x) / 2, -47.0 - 2.0 * i, zr), (E.x - 10, E.y - 1, E.z + 14), (E.x, E.y, E.z + 7), (E.x, E.y, E.z - 2)]
        CABLES.append(wire(f'coax{i}', pts, M_COAX, r=COAX_R))
    # GPIO harness: hood exits (x = HOOD_TOP), one every 4 mm along z
    lemos = sorted([c for c in BRD['comps'] if c['fp'] == 'LEMO_EPL00'], key=lambda c: -comp_matrix(c).translation.x)
    exits = [HZ0 + 3.0 + 4.2 * k for k in range(5)]
    BM = {k: bmesh.new() for k in BM_MATS}
    for k, c in enumerate(lemos):
        Mc = comp_matrix(c)
        pcyl(Mc, 3.35, 13.0, 'chrome', 'x', 15.0, 3.6, 0, 40)          # LEMO FFA.00 plug body
        pcyl(Mc, 3.6, 3.0, 'chrome', 'x', 18.5, 3.6, 0, 40)            # latch sleeve
        pcyl(Mc, 2.5, 10.0, 'plastic', 'x', 26.5, 3.6, 0, 32)           # strain-relief boot
        pcyl(Mc, 2.7, 2.0, 'nylon' if False else 'plastic', 'x', 22.5, 3.6, 0, 32)
        P0 = Mc @ Vector((31.0, 3.6, 0)) / MM
        P1 = Mc @ Vector((40.0, 3.6, 0)) / MM
        zx = exits[k]
        gy = -186.0 - 3.2 * k                          # run along the front, one cable beside the other
        pts = [tuple(P0), tuple(P1), (P1.x + 6, gy + 4, 8.0), (P1.x + 18, gy, -1.2 + COAX_R),
               (150.0, gy, -1.2 + COAX_R), (182.0 + 3 * k, gy + 18, -1.2 + COAX_R), (200.0 + 3.2 * k, -120.0, -1.2 + COAX_R),
               (206.0 + 3.2 * k, -80.0, 6.0), (210.0 + 3.2 * k, -48.0, 40.0), (212.0 + 3.2 * k, -24.0, 78.0),
               (HOOD_TOP + 6 + 2.0 * k, PY(26.5) - 4, zx - 14), (HOOD_TOP + 3, PY(26.5), zx - 2), (HOOD_TOP - 1, PY(26.5), zx)]
        CABLES.append(wire(f'hcoax{k}', pts, M_COAX, r=COAX_R))
    # J6: 3-way housing + 3-core cable
    j6 = [c for c in BRD['comps'] if c['ref'] == 'J6'][0]
    Mc = comp_matrix(j6)
    pbox(Mc, 7.7, 14.0, 2.6, 'plastic', 2.54, 2.6 + 7.0, 0)
    P0 = Mc @ Vector((2.54, 16.0, 0)) / MM
    zx = exits[4]
    pts = [tuple(P0), (P0.x, P0.y, P0.z + 8), (P0.x + 14, P0.y + 6, P0.z + 16), (170.0, -96.0, 60.0),
           (204.0, -60.0, 76.0), (214.0, -30.0, 92.0), (HOOD_TOP + 14, PY(26.5) - 4, zx - 12), (HOOD_TOP + 3, PY(26.5), zx - 2), (HOOD_TOP - 1, PY(26.5), zx)]
    CABLES.append(wire('hi2c', pts, mat_simple('i2c_cable', (0.04, 0.04, 0.045), 0.5), r=1.5))
    for k2, bmk in BM.items():
        if len(bmk.verts):
            o = mesh_obj('plug_' + k2, bmk)
            setmat(o, BM_MATS[k2])
            HARNESS.append(o)
    # Pi power: micro-USB plug in PWR, cable down to the table
    up = box('usbplug', PT - 0.5, PT + 6.5, PY(-1.0) - 14.0, PY(-1.0) + 0.5, PZ(54) - 5.5, PZ(54) + 5.5)
    bevel(up, 1.5, 2)
    setmat(up, BM_MATS['plastic'])
    COMPUTE.append(up)
    pts = [(PT + 3, PY(-1.0) - 13.0, PZ(54)), (PT + 3, PY(-1.0) - 24.0, PZ(54) - 2), (PT + 8, -60.0, 110.0),
           (196.0, -70.0, 50.0), (194.0, -58.0, 14.0), (196.0, -44.0, -1.2 + 1.6), (250.0, 30.0, -1.2 + 1.6), (330.0, 160.0, -1.2 + 1.6)]
    CABLES.append(wire('pipwr', pts, M_COAX, r=1.6))
    # 5 V supply into J3 (bottom of the board), down to the table
    E = KK_IN['J3'] / MM
    for j, (dy, mt) in enumerate(((-1.27, M_WIRE_R), (1.27, M_WIRE_K))):
        pts = [(E.x + dy, E.y, E.z - 2), (E.x + dy, E.y, E.z + 5), (E.x + dy + 9, E.y - 3, E.z + 6),
               (122.0 + dy, -72.0, 44.0), (146.0 + dy, -98.0, 22.0), (160.0 + dy, -106.0, -2 + W_R),
               (176.0 + dy, -96.0, -2 + W_R), (230.0 + dy, -20.0, -2 + W_R), (300.0 + dy, 140.0, -2 + W_R)]
        CABLES.append(wire(f'pwr{j}', pts, mt, r=W_R))

# ---------------------------------------------------------------- compute module opened
if OPEN:
    for ob in LID_PARTS:
        ob.location.x += m(48)
    for ob in HARNESS:
        ob.location.x += m(80)
    for ob in CABLES:
        if ob.name.startswith('hcoax') or ob.name.startswith('hi2c'):
            ob.hide_render = True
    for ob in HARNESS:
        if ob.name.startswith('plug_'):
            ob.location.x -= m(80)

# ---------------------------------------------------------------- exploded offsets
if EXPLODED:
    B, U = 115.0, 60.0

    def xmean(ob):
        return sum(v.co.x for v in ob.data.vertices) / len(ob.data.vertices) / MM

    def move(ob, dx, dz):
        ob.location.x += m(dx)
        ob.location.z += m(dz)

    UPX, CLX, SPX, FTX = 70.0, 20.0, 45.0, 70.0

    def zmin(ob):
        return min(v.co.z for v in ob.data.vertices) / MM

    spacers = {-1.0: [], 1.0: []}
    for ob in list(scene.collection.objects):
        if ob.type != 'MESH':
            continue
        n = ob.name
        side = 1.0 if xmean(ob) > 0 else -1.0
        if ob in MODULE:
            move(ob, 0, B + 30)
            ob.location.y += m(-120)
        elif ob in COMPUTE:
            move(ob, UPX + 45, B + U)
        elif ob in HARNESS:
            move(ob, UPX + 75, B + U)
        elif n.startswith('fpin'):
            move(ob, FTX * side, B + 12)
        elif n.startswith('foot_'):
            move(ob, FTX * side, B)
        elif n.startswith('rubber'):
            move(ob, FTX * side, B - 14)
        elif n.startswith('hprofile'):
            move(ob, 0, B)
        elif n.startswith('tnut'):
            move(ob, 0, B - 16)
        elif n.startswith('bscrew'):
            move(ob, FTX * side, 34)
        elif n.startswith('bolt'):
            move(ob, FTX * side, 26)
        elif n.startswith('upright'):
            move(ob, UPX * side, B + U)
        elif n.startswith('cap_'):
            move(ob, UPX * side, B + U + 40)
        elif n.startswith('clip'):
            move(ob, CLX * side, B + U)
        elif n.startswith('spacer'):
            spacers[side].append(ob)
        elif n.startswith('bar'):
            move(ob, 0, B + U)
    # spacers: own column, spread apart so each piece reads separately
    for side, lst in spacers.items():
        lst.sort(key=zmin)
        for k, ob in enumerate(lst):
            move(ob, SPX * side, B + U + (SOCK_TOP + k * 13.6) - zmin(ob))
    for ob in PCB_PARTS:
        move(ob, 0, B + U + 24)
    for ob in COVERS:
        move(ob, 0, B + U + 46)
    for ob in CCLIPS:
        move(ob, -UPX, B + U)
        ob.location.y += m(-22)

    M_AXIS = mat_simple('axis', (0.25, 0.25, 0.27), 0.7)

    def dashed(x, y, z0, z1):
        z = z0
        while z < z1:
            d = cyl('dash', x, y, 0.28, z, min(z + 4.0, z1), 12)
            setmat(d, M_AXIS)
            d.visible_shadow = False
            z += 6.5

    for x in (UX, -UX):
        sd = 1 if x > 0 else -1
        xo = x + UPX * sd
        xf = x + FTX * sd
        dashed(xf, 0, 26 + 21 + 3, B - 2)                 # screw -> foot
        dashed(xf, 0, B + FOOT_TOP + 4, B + U + UP_Z0 - 3) # foot -> upright
        dashed(sd * -BS_X + FTX * sd, 0, 34 + 8 + 3, B - 2)  # button screw -> foot
        dashed(xo, 0, B + U + UP_Z0 + UP_H + 4, B + U + 40 + UP_Z0 + UP_H - 9)  # upright -> cap
    for x, bs, tn in HW:
        dashed(x, 0, B - 16 + H_Z0 + 5, B + H_Z0 - 1)    # slot nut -> profile

# ---------------------------------------------------------------- floor (shadow catcher)
floor = box('floor', -3000, 3000, -3000, 3000, -3, -2)
floor.is_shadow_catcher = True
setmat(floor, mat_simple('floor', (0.8, 0.8, 0.8), 0.6))

# ---------------------------------------------------------------- world & lights
world = bpy.data.worlds.new('w')
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes['Background']
wn = world.node_tree
wtc = wn.nodes.new('ShaderNodeTexCoord')
wsep = wn.nodes.new('ShaderNodeSeparateXYZ')
wn.links.new(wtc.outputs['Generated'], wsep.inputs[0])
wmr = wn.nodes.new('ShaderNodeMapRange')
wmr.inputs['From Min'].default_value = -0.3
wmr.inputs['From Max'].default_value = 0.9
wmr.inputs['To Min'].default_value = 0.12
wmr.inputs['To Max'].default_value = 1.0
wn.links.new(wsep.outputs['Z'], wmr.inputs['Value'])
wn.links.new(wmr.outputs['Result'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 0.35


def area(name, loc, size, power, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.shape = 'DISK'
    ld.size = size
    ld.energy = power
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector((0, 0, 0.12)) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


area('key', (-0.9, -0.9, 1.3), 1.4, 40, (1.0, 0.97, 0.93))
area('fill', (1.2, -0.7, 0.6), 1.6, 14, (0.93, 0.96, 1.0))
area('rim', (0.3, 1.2, 1.0), 1.2, 22)
area('top', (0.0, 0.0, 1.6), 1.5, 12)

# ---------------------------------------------------------------- camera
cam_d = bpy.data.cameras.new('cam')
cam_d.lens = 70
cam_d.clip_start = 0.002
cam_d.sensor_width = 36
cam = bpy.data.objects.new('cam', cam_d)
scene.collection.objects.link(cam)
if EXPLODED:
    target = Vector((m(20), m(-95), m(190)))
    cam.location = target + Vector((-0.42, -0.86, 0.46)) * 1.55
elif COMPUTE_VIEW:
    target = Vector((m(188), m(-4), m(148)))
    cam.location = target + Vector((0.62, -0.62, 0.42)) * (0.50 if OPEN else 0.46)
else:
    target = Vector((m(28), m(-70), m(104)))
    cam.location = target + Vector((-0.34, -0.88, 0.55)) * 1.30
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------------------------------------------------------------- render
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 8
scene.render.film_transparent = True
scene.render.resolution_x = RES
scene.render.resolution_y = int(RES * (1.0 if EXPLODED else 0.8))
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.filepath = OUT
if not PARTS:
    bpy.ops.render.render(write_still=True)
else:
    import os
    os.makedirs(OUT, exist_ok=True)
    scene.render.resolution_y = int(RES * 0.8)
    cam_d.lens = 85
    flipX = Matrix.Rotation(math.pi, 4, 'X')
    jobs = [  # (file, source object, view direction, print-orientation transform)
        ('piede', 'foot_L', (-0.62, -0.75, 0.55), None),
        ('aggancio_retro', 'clipL1', (-0.80, -0.45, 0.55), None),
        ('aggancio_fronte', 'clipL1', (0.80, -0.45, 0.55), None),
        ('distanziale', 'spacer0', (-0.70, -0.55, 0.60), None),
        ('tappo', 'cap_L', (-0.50, -0.86, 0.75), flipX),
        ('guida_laterale', 'bsupL', (-0.55, -0.75, 0.62), None),
        ('guida_centrale', 'bsupC', (-0.45, -0.80, 0.62), None),
        ('scatola_calcolo', 'cbox', (0.60, -0.60, 0.55), None),
        ('coperchio_calcolo', 'clid', (0.70, -0.45, 0.55), None),
        ('cuffia_gpio', 'hood', (0.65, -0.55, 0.55), None),
        ('copertura', 'cover', (-0.55, -0.75, 0.75), None),
    ]
    for ob in scene.objects:
        if ob.type in ('MESH', 'CURVE') and ob.name != 'floor':
            ob.hide_render = True
    for fname, src, vdir, tf in jobs:
        o = bpy.data.objects[src]
        c = o.copy()
        c.data = o.data.copy()
        scene.collection.objects.link(c)
        c.hide_render = False
        if tf is not None:
            c.data.transform(tf)
        xs = [v.co.x for v in c.data.vertices]; ys = [v.co.y for v in c.data.vertices]; zs = [v.co.z for v in c.data.vertices]
        c.data.transform(Matrix.Translation((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs))))
        c.data.update()
        xs = [v.co.x for v in c.data.vertices]; ys = [v.co.y for v in c.data.vertices]; zs = [v.co.z for v in c.data.vertices]
        ctr = Vector((0, 0, max(zs) / 2))
        r = max((Vector((x, y, z)) - ctr).length for x, y, z in zip(xs, ys, zs))
        dist = r / math.sin(math.atan(14.4 / 85)) * (0.85 if fname == 'piede' else 1.0)
        cam.location = ctr + Vector(vdir).normalized() * dist
        cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(OUT, fname + '.png')
        bpy.ops.render.render(write_still=True)
        # STL in print orientation (mm)
        if fname != 'aggancio_fronte':
            bpy.ops.object.select_all(action='DESELECT')
            c.select_set(True)
            bpy.context.view_layer.objects.active = c
            bpy.ops.wm.stl_export(filepath=os.path.join(OUT, fname.replace('_retro', '') + '.stl'),
                                  export_selected_objects=True, global_scale=1000.0, apply_modifiers=True)
        bpy.data.objects.remove(c, do_unlink=True)
