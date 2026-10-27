"""Genera un modello STL stampabile del Cervino (Matterhorn) da dati DEM reali.

Fonte: Copernicus DEM GLO-30 (ESA, ~30 m), tile N45 E007, da
https://copernicus-dem-30m.s3.amazonaws.com/

L'area attorno alla vetta attraversa il parallelo 46 N, quindi servono due tile
(N45 e N46); lo script le scarica da solo nella cartella indicata con --cache.

Uso: python make_cervino_stl.py output.stl [--size 180] [--km 6] [--exag 1.0]
"""
import argparse
import os
import urllib.request
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling, transform as warp_transform
from rasterio.merge import merge
from rasterio.transform import from_origin

SUMMIT = (7.6586, 45.9763)  # lon, lat vetta (4478 m)
UTM32 = "EPSG:32632"
TILE_URL = ("https://copernicus-dem-30m.s3.amazonaws.com/"
            "Copernicus_DSM_COG_10_N{lat}_00_E007_00_DEM/Copernicus_DSM_COG_10_N{lat}_00_E007_00_DEM.tif")


def fetch_tiles(cache):
    os.makedirs(cache, exist_ok=True)
    paths = []
    for lat in (45, 46):
        url = TILE_URL.format(lat=lat)
        p = os.path.join(cache, os.path.basename(url))
        if not os.path.exists(p):
            print("scarico", url)
            urllib.request.urlretrieve(url, p)
        paths.append(p)
    return paths


def load_dem(paths, half_m, n):
    cx, cy = warp_transform("EPSG:4326", UTM32, [SUMMIT[0]], [SUMMIT[1]])
    cx, cy = cx[0], cy[0]
    res = 2 * half_m / n
    srcs = [rasterio.open(p) for p in paths]
    mosaic, mosaic_tf = merge(srcs, bounds=(7.5, 45.85, 7.85, 46.1))
    crs = srcs[0].crs
    for s in srcs:
        s.close()
    dst = np.zeros((n, n), dtype=np.float32)
    dst_tf = from_origin(cx - half_m, cy + half_m, res, res)
    reproject(mosaic[0], dst, src_transform=mosaic_tf, src_crs=crs,
              dst_transform=dst_tf, dst_crs=UTM32, resampling=Resampling.cubic)
    return dst, res


def write_stl(path, z_mm, size_mm):
    n = z_mm.shape[0]
    step = size_mm / (n - 1)
    xs = np.arange(n) * step
    ys = (n - 1 - np.arange(n)) * step  # riga 0 = nord = y massimo
    X, Y = np.meshgrid(xs, ys)
    top = np.stack([X, Y, z_mm], -1)  # (n, n, 3)

    facets = []
    # superficie (normali verso l'alto: ordine antiorario visto dall'alto)
    p00, p01 = top[:-1, :-1], top[:-1, 1:]
    p10, p11 = top[1:, :-1], top[1:, 1:]
    facets.append(np.stack([p00, p10, p01], -2).reshape(-1, 3, 3))
    facets.append(np.stack([p01, p10, p11], -2).reshape(-1, 3, 3))

    # bordo in senso antiorario visto dall'alto
    border = np.concatenate([
        top[-1, :],          # sud, ovest->est
        top[::-1, -1][1:],   # est, sud->nord
        top[0, ::-1][1:],    # nord, est->ovest
        top[:-1, 0][1:],     # ovest, nord->sud (senza ripetere l'angolo SO)
    ])
    nxt = np.roll(border, -1, axis=0)
    bot, botn = border.copy(), nxt.copy()
    bot[:, 2] = 0
    botn[:, 2] = 0
    facets.append(np.stack([border, bot, nxt], 1))
    facets.append(np.stack([nxt, bot, botn], 1))

    # fondo (normale verso il basso): ventaglio dal centro sugli stessi vertici delle pareti
    centre = np.broadcast_to([size_mm / 2, size_mm / 2, 0.0], bot.shape)
    facets.append(np.stack([centre, botn, bot], 1))

    tri = np.concatenate(facets).astype(np.float32)
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = nrm, tri
    with open(path, "wb") as f:
        f.write(b"Cervino / Matterhorn - Copernicus DEM GLO-30".ljust(80, b" "))
        f.write(np.uint32(len(tri)).tobytes())
        f.write(rec.tobytes())
    return len(tri)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--cache", default="dem_cache", help="cartella per le tile DEM")
    ap.add_argument("--size", type=float, default=180, help="lato modello in mm")
    ap.add_argument("--km", type=float, default=6, help="lato area reale in km")
    ap.add_argument("--exag", type=float, default=1.0, help="esagerazione verticale")
    ap.add_argument("--base", type=float, default=5, help="spessore base in mm sotto il punto più basso")
    ap.add_argument("--grid", type=int, default=400, help="punti per lato")
    a = ap.parse_args()

    elev, res = load_dem(fetch_tiles(a.cache), a.km * 500, a.grid)
    scale = a.size / (a.km * 1000)  # mm per metro
    z = (elev - elev.min()) * scale * a.exag + a.base
    ntri = write_stl(a.out, z, a.size)
    print(f"quota min {elev.min():.0f} m, max {elev.max():.0f} m, risoluzione griglia {res:.1f} m")
    print(f"scala 1:{1/scale*1000:,.0f}  -> {a.size:.0f} x {a.size:.0f} x {z.max():.1f} mm, {ntri} triangoli")


if __name__ == "__main__":
    main()
