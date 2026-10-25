#!/usr/bin/env python3
"""Render a colori di un gruppo di cubi montati, come escono con la stampa
a cambio filamento: corpo neutro e testi in rilievo di un altro colore.
Con CORNICE=1 nell'ambiente anche la cornice frontale prende il colore
della categoria (terzo filamento, facoltativo).

uso: render_tavola.py uscita.png riga0 riga1 col0 col1 [azimut elevazione]
"""
import os
import subprocess
import sys
import tempfile

import matplotlib
import numpy as np
import trimesh

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tavola  # noqa: E402

CORPO = "#ece8e1"
TESTO = "#26282b"
PAVIMENTO = "#3b3d40"
CORNICE_SP = tavola.quote_dal_modello()["cornice"]


def mesh_cubo(c, d):
    out = os.path.join(d, c["id"] + ".stl")
    cmd = tavola.comando_openscad(c, "corpo_appeso", out)
    subprocess.run(cmd, check=True, capture_output=True)
    return trimesh.load(out)


def rendi(uscita, r0, r1, k0, k1, az=-28, el=16, px=1600):
    cubi = [c for c in tavola.con_vicini(tavola.tutti_i_cubi())
            if r0 <= c["riga"] <= r1 and k0 <= c["colonna"] <= k1]
    passo = 100.5
    with tempfile.TemporaryDirectory() as d:
        pav = os.path.join(d, "pav.stl")
        subprocess.run(["openscad", "-o", pav, "-D", 'parte="pavimento_appeso"', tavola.SCAD],
                       check=True, capture_output=True)
        pav = trimesh.load(pav)
        scena = []
        for c in cubi:
            off = np.array([(c["colonna"] - k0) * passo, 0, (r1 - c["riga"]) * passo])
            col = tavola.COLORI_CORNICE.get(c["categoria"], "#999999") \
                if os.environ.get("CORNICE") == "1" else CORPO
            scena.append((mesh_cubo(c, d), off, col))
            scena.append((pav, off, None))
    tutti = np.vstack([m.vertices + o for m, o, _ in scena])
    centro = (tutti.min(0) + tutti.max(0)) / 2
    a, b = np.radians(az), np.radians(el)
    rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    R = rx @ rz
    proiettati = (tutti - centro) @ R.T
    estensione = max(np.ptp(proiettati[:, 0]), np.ptp(proiettati[:, 2])) * 1.08
    scala = px / estensione
    H = int(np.ptp(proiettati[:, 2]) * 1.08 * scala) + 40
    W = px
    img = np.ones((H, W, 3)) * np.array(matplotlib.colors.to_rgb("#f3f1ec"))
    zb = np.full((H, W), np.inf)
    luce = np.array([-0.5, -0.75, 0.55]); luce /= np.linalg.norm(luce)
    rgb = lambda h: np.array(matplotlib.colors.to_rgb(h))
    for m, off, cornice in scena:
        mondo = m.vertices + off
        v = (mondo - centro) @ R.T
        n = m.face_normals @ R.T
        y_loc = m.vertices[:, 1]
        for f, nn, nw in zip(m.faces, n, m.face_normals):
            if nn[1] > 0.02:
                continue
            p = v[f]
            xs = p[:, 0] * scala + W / 2
            ys = H / 2 - p[:, 2] * scala
            x0, x1 = max(int(xs.min()), 0), min(int(xs.max()) + 1, W - 1)
            y0, y1 = max(int(ys.min()), 0), min(int(ys.max()) + 1, H - 1)
            if x0 > x1 or y0 > y1:
                continue
            X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(den) < 1e-9:
                continue
            w0 = ((ys[1] - ys[2]) * (X - xs[2]) + (xs[2] - xs[1]) * (Y - ys[2])) / den
            w1 = ((ys[2] - ys[0]) * (X - xs[2]) + (xs[0] - xs[2]) * (Y - ys[2])) / den
            w2 = 1 - w0 - w1
            dentro = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            prof = w0 * p[0, 1] + w1 * p[1, 1] + w2 * p[2, 1]
            zbs = zb[y0:y1 + 1, x0:x1 + 1]
            ok = dentro & (prof < zbs)
            if not ok.any():
                continue
            lum = 0.38 + 0.62 * max(0.0, float(nn @ luce))
            if cornice is None:
                colore = np.broadcast_to(rgb(PAVIMENTO) * lum, ok.shape + (3,))
            else:
                # profondità locale del punto: decide il filamento (strati di stampa)
                yl = w0 * y_loc[f[0]] + w1 * y_loc[f[1]] + w2 * y_loc[f[2]]
                colore = np.where((yl < -0.05)[..., None], rgb(TESTO),
                                  np.where((yl < CORNICE_SP - 0.05)[..., None],
                                           rgb(cornice), rgb(CORPO))) * lum
            zbs[ok] = prof[ok]
            img[y0:y1 + 1, x0:x1 + 1][ok] = np.clip(colore[ok], 0, 1)
    plt.imsave(uscita, img)
    print(uscita)


if __name__ == "__main__":
    a = sys.argv
    extra = [float(x) for x in a[6:8]]
    rendi(a[1], int(a[2]), int(a[3]), int(a[4]), int(a[5]), *extra)
