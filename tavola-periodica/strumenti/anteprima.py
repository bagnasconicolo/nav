#!/usr/bin/env python3
"""Piccolo renderer software (z-buffer) per anteprime PNG dei cubi.

uso: anteprima.py uscita.png vista file1.stl:#colore [file2.stl:#colore ...]
viste: fronte, tre_quarti, retro, sotto, fascia
"""
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

VISTE = {  # (azimut, elevazione, zoom, centro z)
    "fronte": (0, 0, 1.0, 50),
    "tre_quarti": (-32, 22, 1.0, 50),
    "retro": (150, 20, 1.0, 50),
    "sotto": (-35, -35, 1.0, 50),
    "fascia": (-8, 18, 2.2, 12),
    "sezione": (90, 0, 1.0, 50),
    "alto": (-25, 55, 1.0, 50),
}


def ruota(az, el):
    a, b = np.radians(az), np.radians(el)
    # camera che guarda verso +y (il fronte del cubo è a y=0)
    rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    return rx @ rz


def rendi(uscita, vista, voci, px=1100):
    az, el, zoom, cz = VISTE[vista]
    R = ruota(az, el)
    luce = np.array([-0.45, -0.8, 0.6]); luce /= np.linalg.norm(luce)
    img = np.ones((px, px, 3)) * np.array([0.96, 0.95, 0.93])
    zb = np.full((px, px), np.inf)
    scala = px / 175 * zoom
    for percorso, colore in voci:
        m = trimesh.load(percorso)
        v = (m.vertices - np.array([50, 50, cz])) @ R.T   # vista: x destra, y profondità, z su
        n = m.face_normals @ R.T
        rgb = np.array(matplotlib.colors.to_rgb(colore))
        # facce sul piano di taglio della vista "sezione" (x = 50): colore a parte
        taglio = np.all(np.abs(m.vertices[m.faces][:, :, 0] - 50) < 1e-3, axis=1) \
            if vista == "sezione" else np.zeros(len(m.faces), bool)
        for f, nn, tg in zip(m.faces, n, taglio):
            if nn[1] > 0.02:      # faccia rivolta lontano dalla camera
                continue
            p = v[f]
            xs = p[:, 0] * scala + px / 2
            ys = px / 2 - p[:, 2] * scala
            d = p[:, 1]
            x0, x1 = max(int(xs.min()), 0), min(int(xs.max()) + 1, px - 1)
            y0, y1 = max(int(ys.min()), 0), min(int(ys.max()) + 1, px - 1)
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
            if not dentro.any():
                continue
            prof = w0 * d[0] + w1 * d[1] + w2 * d[2]
            zbs = zb[y0:y1 + 1, x0:x1 + 1]
            ok = dentro & (prof < zbs)
            lum = 0.40 + 0.60 * max(0.0, float(nn @ luce))
            zbs[ok] = prof[ok]
            col = np.array([0.80, 0.33, 0.25]) if tg else rgb * lum
            img[y0:y1 + 1, x0:x1 + 1][ok] = np.clip(col, 0, 1)
    plt.imsave(uscita, img)


if __name__ == "__main__":
    voci = [(a.rsplit(":", 1)[0], a.rsplit(":", 1)[1]) for a in sys.argv[3:]]
    rendi(sys.argv[1], sys.argv[2], voci)
