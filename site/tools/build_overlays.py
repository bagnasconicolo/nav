#!/usr/bin/env python3
"""
Rigenera gli overlay georeferenziati per la mappa da campo.

Legge tutti i GeoTIFF (.tif/.tiff) in EPSG:4326 (WGS84) north-up presenti nella
cartella indicata, li converte in immagini web ottimizzate (JPEG, o WEBP se hanno
trasparenza) dentro site/overlays/, e riscrive site/overlays.js con i bounding box.

Uso:
    python3 build_overlays.py /percorso/cartella/con/tif    [--maxdim 3200]

Poi ricarica la pagina: le nuove foto appaiono nel pannello Livelli.
Nota: sono supportati solo GeoTIFF in EPSG:4326, north-up (pixel scale + tiepoint).
"""
import sys, os, glob, json, argparse
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
OUT_DIR = os.path.join(SITE, "overlays")

def prettify(base):
    return base.replace("_modified", "").replace("_", " ").strip().title()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="cartella con i GeoTIFF")
    ap.add_argument("--maxdim", type=int, default=3200, help="lato massimo in px (default 3200)")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    tifs = sorted(glob.glob(os.path.join(args.src, "*.tif")) +
                  glob.glob(os.path.join(args.src, "*.tiff")))
    if not tifs:
        print("Nessun .tif trovato in", args.src); sys.exit(1)

    manifest = []
    for f in tifs:
        im = Image.open(f)
        W, H = im.size
        meta = im.tag_v2
        if 33550 not in meta or 33922 not in meta:
            print("  SALTO (non georef. semplice):", os.path.basename(f)); continue
        sx, sy, _ = meta[33550]
        tp = meta[33922]
        west, north = tp[3], tp[4]
        east, south = west + W * sx, north - H * sy
        has_alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info

        scale = min(1.0, args.maxdim / max(W, H))
        if scale < 1.0:
            im = im.resize((round(W * scale), round(H * scale)), Image.LANCZOS)

        base = os.path.splitext(os.path.basename(f))[0].replace(" ", "_")
        if has_alpha:
            out = os.path.join(OUT_DIR, base + ".webp")
            im.save(out, "WEBP", quality=82, method=5)
        else:
            out = os.path.join(OUT_DIR, base + ".jpg")
            im.convert("RGB").save(out, "JPEG", quality=82, optimize=True)

        manifest.append({
            "id": base, "name": prettify(base), "zone": "",
            "file": "overlays/" + os.path.basename(out),
            "bounds": [[south, west], [north, east]],
            "center": [(south + north) / 2, (west + east) / 2],
        })
        print("  OK %-40s %.2f MB" % (os.path.basename(out), os.path.getsize(out) / 1e6))

    with open(os.path.join(SITE, "overlays.js"), "w") as fp:
        fp.write("window.OVERLAYS = " + json.dumps(manifest, indent=2) + ";\n")
    print("\nScritti %d overlay -> overlays.js" % len(manifest))

if __name__ == "__main__":
    main()
