"""Printability check for the STL parts (print orientation, mm).

For every part: bed fit (Ender 3: 220 x 220 x 250), downward faces steeper than 45 deg that are
not on the bed (would need support), and horizontal down-facing patches (bridges) with their span.
Usage: python check_print.py pezzi/*.stl
"""
import struct
import sys
from collections import defaultdict

import numpy as np

BED = (220.0, 220.0, 250.0)


def load(path):
    d = open(path, 'rb').read()
    n = struct.unpack('<I', d[80:84])[0]
    rec = np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    return rec['v'].reshape(-1, 3, 3).astype(float)


def components(tris):
    """connected patches of triangles sharing a vertex"""
    parent = list(range(len(tris)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    seen = {}
    for i, t in enumerate(tris):
        for p in t:
            key = tuple(np.round(p, 3))
            if key in seen:
                a, b = find(i), find(seen[key])
                parent[a] = b
            else:
                seen[key] = i
    groups = defaultdict(list)
    for i in range(len(tris)):
        groups[find(i)].append(i)
    return list(groups.values())


def check(path):
    t = load(path)
    zmin = t[:, :, 2].min()
    size = t.reshape(-1, 3).max(0) - t.reshape(-1, 3).min(0)
    e1, e2 = t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]
    nrm = np.cross(e1, e2)
    area = np.linalg.norm(nrm, axis=1) / 2
    nz = nrm[:, 2] / np.maximum(np.linalg.norm(nrm, axis=1), 1e-12)
    zc = t[:, :, 2].mean(1)
    above = zc > zmin + 1.0                               # the first mm is the 0.6 mm bed chamfer
    steep = (nz < -0.72) & (nz >= -0.985) & above          # > ~46 deg from vertical, not flat
    flat = (nz < -0.985) & above                          # bridges
    spans = []
    if flat.any():
        idx = np.where(flat)[0]
        for g in components(t[idx]):
            pts = t[idx[g]].reshape(-1, 3)
            ext = pts.max(0) - pts.min(0)
            spans.append(min(ext[0], ext[1]))
    fits = all(size[i] <= BED[i] - 4 for i in range(3))
    return dict(name=path.split('/')[-1], size=size, fits=fits, steep=area[steep].sum(),
                bridge_max=max(spans) if spans else 0.0, bridges=len(spans))


if __name__ == '__main__':
    print(f"{'pezzo':24s} {'ingombro (mm)':>22s} {'piatto':>7s} {'sbalzi>45° (mm²)':>17s} {'ponti':>6s} {'luce max':>9s}")
    for p in sys.argv[1:]:
        r = check(p)
        s = r['size']
        print(f"{r['name']:24s} {s[0]:6.1f} x {s[1]:5.1f} x {s[2]:5.1f} {'ok' if r['fits'] else 'NO':>7s} "
              f"{r['steep']:17.1f} {r['bridges']:6d} {r['bridge_max']:8.1f}")
