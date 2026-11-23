"""Genera gli STL dei formati standard (stessa geometria del file .scad)."""
import os, numpy as np, manifold3d as m3d, trimesh

GRID, GAP = 25.0, 0.5
WALL, FLOOR, R, FIL, CH = 1.8, 1.6, 3.0, 2.0, 0.6
LAB_H, LAB_D = 8.0, 0.4
SEG = 48

def rrect(l, w, r, h):
    r = max(min(r, l/2-0.01, w/2-0.01), 0.01)
    cs = m3d.CrossSection.square([l-2*r, w-2*r], center=True).offset(r, m3d.JoinType.Round, circular_segments=SEG)
    return m3d.Manifold.extrude(cs, h)

def hull2(a, b): return m3d.Manifold.batch_hull([a, b])

def box(cx, cy, H):
    L, W = cx*GRID-GAP, cy*GRID-GAP
    ext = hull2(rrect(L-2*CH, W-2*CH, R-CH, 0.01),
                rrect(L, W, R, H-CH).translate([0,0,CH]))
    li, wi, ri = L-2*WALL, W-2*WALL, max(R-WALL, 0.5)
    cav = hull2(rrect(li-2*FIL, wi-2*FIL, max(ri-FIL,0.5), 0.01).translate([0,0,FLOOR]),
                rrect(li, wi, ri, H).translate([0,0,FLOOR+FIL]))
    s = ext - cav
    if H >= LAB_H + 6:
        lw = L - 2*R - 2
        s = s - m3d.Manifold.cube([lw, 1+LAB_D, LAB_H]).translate([-lw/2, -W/2-1, (H-LAB_H)/2])
    mesh = s.to_mesh()
    return trimesh.Trimesh(mesh.vert_properties[:, :3], mesh.tri_verts)

FORMATI = [  # (celle_x, celle_y, altezza, nome)
    (1, 1, 16, "micromount"),
    (2, 1, 18, "micro-doppia"),
    (2, 2, 22, "thumbnail"),
    (3, 2, 25, "miniatura"),
    (3, 3, 28, "miniatura-grande"),
    (4, 2, 25, "small-cabinet-rett"),
    (4, 4, 32, "small-cabinet"),
]

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")
    os.makedirs(out, exist_ok=True)
    for cx, cy, h, nome in FORMATI:
        t = box(cx, cy, h)
        fn = f"scatola_{cx}x{cy}_{nome}_{cx*GRID-GAP:g}x{cy*GRID-GAP:g}x{h}.stl"
        t.export(os.path.join(out, fn))
        print(fn, "watertight" if t.is_watertight else "NON watertight", f"{t.volume/1000:.1f} cm3")
