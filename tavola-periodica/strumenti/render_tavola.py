#!/usr/bin/env python3
"""Render a colori di un gruppo di cubi montati, come escono con la stampa
a cambio filamento in altezza: corpo scuro, lastra frontale chiara, testi
in rilievo scuri. Con CORNICE=1 nell'ambiente il fronte prende invece il
colore della categoria.

Con USA_STL=1 usa gli STL già esportati in stl/ invece di rigenerarli
(molto più veloce per la tavola completa) e disegna anche il pannello.

uso: render_tavola.py uscita.png riga0 riga1 col0 col1 [azimut elevazione [pixel]]
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

CORPO = "#2c2e31"       # corpo e nicchia
FRONTE = "#ece8e1"      # lastra frontale
TESTO = "#26282b"
LEGNO = "#d9c4a0"       # pannello in multistrato
CORNICE_SP = tavola.quote_dal_modello()["cornice"]


def mesh_cubo(c, d):
    if os.environ.get("USA_STL") == "1":
        # STL di stampa (retro sul piatto) -> posizione appesa: (X, Y, Z) -> (X, P - Z, Y)
        m = trimesh.load(os.path.join(tavola.DIR_STL, c["id"] + ".stl"))
        P = tavola.quote_dal_modello()["profondita"]
        v = m.vertices
        return trimesh.Trimesh(np.column_stack([v[:, 0], P - v[:, 2], v[:, 1]]), m.faces)
    out = os.path.join(d, c["id"] + ".stl")
    cmd = tavola.comando_openscad(c, "corpo_appeso", out)
    # parametri in più per provare varianti: SCAD_D="nome_maiuscolo=true;h_nome=3"
    for d in filter(None, os.environ.get("SCAD_D", "").split(";")):
        cmd[-1:-1] = ["-D", d]
    subprocess.run(cmd, check=True, capture_output=True)
    return trimesh.load(out)


def rendi(uscita, r0, r1, k0, k1, az=-28, el=16, px=1600):
    cubi = [c for c in tavola.con_vicini(tavola.tutti_i_cubi())
            if r0 <= c["riga"] <= r1 and k0 <= c["colonna"] <= k1]
    passo = tavola.quote_dal_modello()["lato"] + tavola.GIOCO_PANNELLO
    # tappo sulla vite, a filo del mozzo
    q = tavola.quote_dal_modello()
    y_tappo, d_tappo, h_tappo = q["tappo"]
    tappo = trimesh.creation.cylinder(radius=d_tappo / 2, height=h_tappo, sections=48)
    tappo.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    tappo.apply_translation([q["vite"][0], y_tappo + h_tappo / 2, q["vite"][1]])
    with tempfile.TemporaryDirectory() as d:
        scena = []
        for c in cubi:
            off = np.array([(c["colonna"] - k0) * passo, 0, (r1 - c["riga"]) * passo])
            col = tavola.COLORI_CORNICE.get(c["categoria"], "#999999") \
                if os.environ.get("CORNICE") == "1" else FRONTE
            scena.append((mesh_cubo(c, d), off, col))
            scena.append((tappo, off, CORPO))
    if os.environ.get("USA_STL") == "1":
        # pannello dietro ai cubi, con un bordo di 60 mm
        q = tavola.quote_dal_modello()
        w = (k1 - k0 + 1) * passo + 100
        h = (r1 - r0 + 1) * passo + 100
        pannello = trimesh.creation.box(extents=[w, 18, h])
        pannello.apply_translation([w / 2 - 50, q["profondita"] + 9.5, h / 2 - 50])
        scena.append((pannello, np.zeros(3), LEGNO))
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
            if cornice in (LEGNO, CORPO):
                colore = np.broadcast_to(rgb(cornice) * lum, ok.shape + (3,))
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
    extra = [float(x) for x in a[6:8]] + [int(x) for x in a[8:9]]
    rendi(a[1], int(a[2]), int(a[3]), int(a[4]), int(a[5]), *extra)
