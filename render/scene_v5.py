import bpy, bmesh, math, sys
from mathutils import Vector

RES = int(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else 800
SAMPLES = int(sys.argv[sys.argv.index('--') + 2]) if '--' in sys.argv else 64
OUT = sys.argv[sys.argv.index('--') + 3] if '--' in sys.argv else '/tmp/r.png'
MODE = sys.argv[sys.argv.index('--') + 4] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 4 else 'assembled'
EXPLODED = MODE == 'exploded'
PARTS = MODE == 'parts'
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
    # --- 2-pole MK terminal block, wire entries facing front (-y)
    tx0, tx1 = -126.0, -116.0
    ty0, ty1 = y0 - 0.6, y0 + 7.6
    term = box('term', tx0, tx1, ty0, ty1, zp, zp + 8.5)
    # sloped/stepped top at the front
    step = prism('step', [(ty0 - 1, zp + 6.2), (ty0 + 2.5, zp + 9), (ty0 - 1, zp + 9)], tx0 - 1, tx1 + 1, axis='x')
    boolean(term, step)
    for i, cx in enumerate([tx0 + 2.5, tx0 + 7.5]):
        hole = box('wh', cx - 1.6, cx + 1.6, ty0 - 1, ty0 + 4.5, zp + 1.6, zp + 4.6)
        boolean(term, hole)
        sh = cyl('sh', cx, ty0 + 4.6, 1.75, zp + 6.5, zp + 10, 32)
        boolean(term, sh)
    # separation groove between the poles
    groove = box('gr', tx0 + 4.85, tx0 + 5.15, ty0 - 1, ty1 + 1, zp + 3, zp + 10)
    boolean(term, groove)
    bevel(term, 0.25, 1)
    setmat(term, M_TERM)
    smooth(term, 30)
    parts.append(term)
    for cx in [tx0 + 2.5, tx0 + 7.5]:
        scr = cyl('screw', cx, ty0 + 4.6, 1.6, zp + 6.6, zp + 7.6, 32)
        slot = box('ss', cx - 2, cx + 2, ty0 + 4.6 - 0.3, ty0 + 4.6 + 0.3, zp + 7.2, zp + 8)
        boolean(scr, slot)
        setmat(scr, M_SCREW)
        parts.append(scr)
        # clamp inside wire entry
        ENTRIES.append((cx, ty0, zp + 3.1, zc))
        cl = box('clamp', cx - 1.4, cx + 1.4, ty0 + 2.0, ty0 + 4.4, zp + 1.7, zp + 4.5)
        setmat(cl, M_SCREW)
        parts.append(cl)
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
    boolean(cov, box('win', tx0 - 0.4, tx1 + 0.4, y0 - 3, ty1 + 0.4, zt - 1, zp + 10))
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
FIL_R = 18.0                 # fillet radius between block and plate
CH_W, CH_D = 8.0, 4.0        # cable channel width / depth
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
    boolean(foot, prism('chan', pts, cx - CH_W / 2, cx + CH_W / 2, axis='x'))
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


# ---------------------------------------------------------------- cable clips (front slot, left upright)
def make_cable_clip(name, zc):
    x = UX
    ring = cyl(name, x, SH_Y, SH_R + 1.6, zc - 4, zc + 4, 48)
    boolean(ring, box('stem', x - 3, x + 3, -UP / 2 - 0.1 - 6.2, -UP / 2 + 0.1, zc - 4, zc + 4), 'UNION')
    bevel(ring, 0.6, 2)
    boolean(ring, cyl('rin', x, SH_Y, SH_R + 0.15, zc - 6, zc + 6, 48))
    boolean(ring, box('gap', x - 2.4, x + 2.4, SH_Y - 8, SH_Y - 1.0, zc - 6, zc + 6))
    # T tongue into the slot (face at y = -UP/2)
    f = -UP / 2
    boolean(ring, box('neck', x - 2.5, x + 2.5, f - 0.2, f + 2.0, zc - 4, zc + 4), 'UNION')
    boolean(ring, box('head', x - 3.7, x + 3.7, f + 1.95, f + 4.0, zc - 4, zc + 4), 'UNION')
    setmat(ring, M_BASE)
    smooth(ring, 35)
    return ring


CCLIPS = [make_cable_clip(f'cclip{k}', z) for k, z in enumerate((36.0, 80.0, 150.0))]

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
    SH_TOP = BAR_Z[2] - 14.0
    for i, zc in enumerate(BAR_Z):
        ents = [e for e in ENTRIES if e[3] == zc]
        zj = SH_TOP if i == 2 else zc - 12.0
        for j, (cx, ty0, ze, _) in enumerate(ents):
            dy = -1.9 * j
            mat = M_WIRE_R if j == 0 else M_WIRE_K
            pts = [(cx, ty0 + 3.0, ze), (cx, ty0 - 4.0, ze),
                   (cx - 6, ty0 - 10.0 + dy, ze - 2),
                   (UX + 16, -28.0 + dy, zc - 5),
                   (UX + 4.0, SH_Y - 3.0 + dy * 0.5, zj + 2),
                   (UX + 0.6 * (1 - 2 * j), SH_Y + 0.4 * dy, zj - 4)]
            CABLES.append(wire(f'wire{i}{j}', pts, mat))
        # heat-shrink sleeve where the pair enters the sheath
        hs = cyl('shrink', UX, SH_Y, SH_R + 0.6, zj - 7, zj + (0.0 if i == 2 else 1.0), 40)
        bevel(hs, 0.4, 2)
        setmat(hs, M_SHRINK)
        CABLES.append(hs)
    # braided sheath: down the front of the left upright, into the foot channel, out on the table
    R, d = FIL_R, CH_D
    rc = R + d - SH_R - 0.2
    sp = [(UX, SH_Y, SH_TOP - 2), (UX, SH_Y, 80.0), (UX, SH_Y, FOOT_TOP + 2)]
    for k in (0, 3, 6, 9, 12, 15, 16):
        t = math.radians(90 * k / 16)
        sp.append((UX, -(20 + R) + rc * math.cos(t), FOOT_H + R - rc * math.sin(t)))
    sp += [(UX, -56.0, FOOT_H - d + SH_R - 1.6), (UX, -75.0, 5 - d + SH_R + 0.2), (UX - 2, -86.0, -2 + SH_R + 0.4),
           (UX - 8, -104.0, -2 + SH_R), (UX - 60, -150.0, -2 + SH_R), (UX - 260, -230.0, -2 + SH_R)]
    CABLES.append(wire('sheath', sp, M_SHEATH, r=SH_R))

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
        if n.startswith('foot_'):
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
    target = Vector((m(-6), m(0), m(222)))
    cam.location = target + Vector((-0.50, -0.86, 0.40)) * 1.45
else:
    target = Vector((m(-12), m(-10), m(118)))
    cam.location = target + Vector((-0.50, -0.86, 0.42)) * 1.02
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
        ('copertura', 'cover', (-0.55, -0.75, 0.75), None),
        ('clip_cavo', 'cclip0', (-0.60, -0.70, 0.55), None),
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
