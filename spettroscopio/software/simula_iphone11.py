#!/usr/bin/env python3
"""
simula_iphone11.py — simulazione fisica di ciò che registra la fotocamera principale
di un iPhone 11 montata sullo spettroscopio (reticolo DVD in trasmissione).

Catena simulata
  sorgente S(λ)  ->  fenditura 50 µm × 6 mm (bordi imperfetti, granelli di polvere)
  -> collimatore piano-convesso borosilicato f=36 mm (dispersione: fuoco che varia con λ)
  -> reticolo DVD d=740 nm, tracciamento vettoriale esatto (diffrazione conica => "smile"),
     efficienza di fase sinusoidale J_m²(a), ordini 1 e 2, luce diffusa
  -> obiettivo iPhone 11 wide: f=4.25 mm, f/1.8, focheggiato a ∞ (diffrazione + aberrazioni)
  -> sensore 4032×3024, pixel 1.4 µm, Bayer RGGB, QE + filtro IR, rumore shot/lettura
  -> ISP: demosaicizzazione, bilanciamento luce diurna, matrice colore, curva tonale,
     nitidezza, JPEG.

Uso:  python3 simula_iphone11.py [--out cartella]
"""
import argparse, math, os
import numpy as np
from scipy.ndimage import gaussian_filter, uniform_filter1d, convolve
from scipy.special import jv
from PIL import Image

# ------------------------------------------------------------------ parametri
D_PITCH = 740.0          # nm
LAMBDA_C = 550.0
ALPHA = math.asin(LAMBDA_C / D_PITCH)
F_COL = 36.0             # mm
SLIT_W = 0.050           # mm
SLIT_L = 6.0             # mm
SLIT_ROT = math.radians(0.35)     # fenditura non perfettamente parallela alle tracce
CAM_ROT = math.radians(0.6)       # telefono leggermente ruotato rispetto alla baionetta
F_CAM, FNUM, PIX = 4.25, 1.8, 1.4e-3
W, H = 4032, 3024
FULL_WELL, READ_E = 6000.0, 2.2
GROOVE_H, N_PC = 165.0, 1.58      # profondità solchi DVD-R (nm), indice policarbonato


def n_boro(l):                     # Cauchy per borosilicato (nd 1.4714, Abbe 65)
    return 1.4605 + 3770.0 / l**2


# ------------------------------------------------------------------ sorgenti
def gauss(l, c, fwhm):
    return np.exp(-4 * math.log(2) * ((l - c) / fwhm) ** 2)


def sorgente_cfl(l):
    """Fluorescente compatta tri-fosforo: righe Hg (strette) + fosfori Eu/Tb + BAM."""
    righe = [(404.66, .30), (407.78, .04), (435.83, 1.0), (546.07, 1.6), (576.96, .22), (579.07, .25)]
    cont = (0.10 * gauss(l, 450, 50)                    # BAM:Eu2+ blu
            + 0.55 * gauss(l, 611.6, 2.6) + 0.12 * gauss(l, 587.5, 3) + 0.10 * gauss(l, 593, 3)
            + 0.09 * gauss(l, 626, 5) + 0.05 * gauss(l, 650, 6) + 0.06 * gauss(l, 707, 6)  # Eu3+
            + 0.40 * gauss(l, 543.5, 7) + 0.18 * gauss(l, 487.7, 6) + 0.10 * gauss(l, 585.5, 6)
            + 0.06 * gauss(l, 620, 7) + 0.03 * gauss(l, 490, 30))                    # Tb3+
    return righe, cont


def sorgente_cielo(l, rng):
    """Luce diurna: corpo nero 5778 K con diffusione di Rayleigh parziale + righe di Fraunhofer."""
    h, c, k = 6.626e-34, 2.998e8, 1.381e-23
    lm = l * 1e-9
    bb = 1 / (lm**5 * (np.exp(h * c / (lm * k * 5778)) - 1))
    s = bb / bb.max() * (550 / l) ** 1.2
    fraunhofer = [  # λ, profondità, larghezza (nm)
        (393.37, .85, 1.2), (396.85, .85, 1.0), (430.8, .35, 1.2), (434.05, .45, .25), (438.4, .3, .15),
        (486.13, .55, .35), (495.8, .2, .1), (516.73, .45, .15), (517.27, .5, .15), (518.36, .55, .18),
        (527.04, .4, .12), (532.8, .2, .1), (589.00, .7, .12), (589.59, .65, .12), (656.28, .72, .2),
        (686.9, .55, .9), (627.7, .25, .6), (630.0, .2, .1)]
    for c0, dpt, wd in fraunhofer:
        s = s * (1 - dpt * np.exp(-0.5 * ((l - c0) / (wd / 2.355)) ** 2) / (1 + ((l - c0) / wd) ** 2 * 0))
    for c0 in rng.uniform(380, 760, 900):  # foresta di righe deboli del Fe e altri metalli
        s = s * (1 - rng.uniform(0.02, 0.18) * np.exp(-0.5 * ((l - c0) / 0.04) ** 2))
    return [], s


def sorgente_led(l):
    """LED bianco: emettitore InGaN 450 nm + fosforo YAG:Ce."""
    return [], 1.0 * gauss(l, 450, 20) + 0.62 * gauss(l, 560, 120) + 0.05 * gauss(l, 640, 60)


# ------------------------------------------------------------------ sensore
def qe(l):
    """Efficienza quantica per canale (stima tipo Sony IMX, incluso filtro IR e UV)."""
    ir = 1 / (1 + np.exp((l - 652) / 9.0))
    uv = 1 / (1 + np.exp((398 - l) / 7.0))
    r = 0.48 * gauss(l, 605, 70) + 0.03 * gauss(l, 450, 60)
    g = 0.55 * gauss(l, 535, 95) + 0.04 * gauss(l, 620, 60)
    b = 0.50 * gauss(l, 455, 75) + 0.02 * gauss(l, 600, 80)
    return np.stack([r, g, b], 0) * (ir * uv)[None]


# ------------------------------------------------------------------ ottica
def direzioni(l_nm, sx, sw, m):
    """Posizione sul sensore (px) di un raggio dal punto (sx, sw) della fenditura, ordine m."""
    sa, ca = math.sin(ALPHA), math.cos(ALPHA)
    u = np.array([0, -sa, ca]); ex = np.array([1.0, 0, 0]); ew = np.array([0, ca, sa])
    cr, sr = math.cos(SLIT_ROT), math.sin(SLIT_ROT)
    ox = sx * cr - sw * sr; ow = sx * sr + sw * cr
    o = ox[..., None] * ex + ow[..., None] * ew
    k = -(F_COL * u) - o
    k = k / np.linalg.norm(k, axis=-1, keepdims=True)
    ky = k[..., 1] - m * l_nm / D_PITCH
    kx = k[..., 0]
    s = 1 - kx**2 - ky**2
    ok = s > 0
    kz = np.sqrt(np.where(ok, s, 1))
    X = F_CAM * ky / kz / PIX
    Y = F_CAM * kx / kz / PIX
    cr, sr = math.cos(CAM_ROT), math.sin(CAM_ROT)
    return W / 2 + X * cr - Y * sr, H / 2 + X * sr + Y * cr, ok


def efficienza(l, m):
    a = math.pi * (N_PC - 1) * GROOVE_H / l
    return jv(m, a) ** 2


def sigma_px(l):
    """Sfocatura (σ, px) per lunghezza d'onda: cromatica del collimatore + diffrazione + obiettivo."""
    n550 = n_boro(LAMBDA_C)
    f_l = F_COL * (n550 - 1) / (n_boro(l) - 1)
    V = 1 / F_COL - 1 / f_l                     # vergenza residua (1/mm), fuoco regolato a 550 nm
    disco = F_CAM * (F_CAM / FNUM) * abs(V) / PIX   # diametro del cerchio di confusione (px)
    airy = 0.42 * l * 1e-6 * FNUM / PIX
    return math.sqrt((disco / 4) ** 2 + airy**2 + 0.65**2 + 0.3**2)   # + obiettivo + reticolo


# ------------------------------------------------------------------ rendering
def renderizza(sorgente, rng, nome):
    l_c = np.arange(372, 790, 0.2)
    righe, cont = sorgente(l_c) if nome != "cielo" else sorgente_cielo(l_c, rng)
    Q = qe(l_c)
    # fenditura: larghezza locale con imperfezioni e due granelli di polvere
    ny = 1400
    sx = np.linspace(-SLIT_L / 2, SLIT_L / 2, ny)
    wloc = 1 + 0.05 * gaussian_filter(np.random.default_rng(7).normal(0, 1, ny), 25) * 6
    for c0, wd, dp in [(-1.3, 0.05, 0.7), (1.9, 0.03, 0.45)]:
        wloc *= 1 - dp * np.exp(-0.5 * ((sx - c0) / wd) ** 2)
    bordo = 1 / (1 + np.exp((np.abs(sx) - SLIT_L / 2 + 0.08) / 0.03))   # bordi della finestra
    wloc *= bordo
    sws = (np.arange(4) + 0.5) / 4 - 0.5                                  # 4 campioni sulla larghezza

    x0, x1, y0, y1 = 0, W, int(H / 2 - 520), int(H / 2 + 520)
    img = np.zeros((3, y1 - y0, x1 - x0), np.float32)
    bande = np.arange(372, 791, 15)

    def deposita(ls, pesi_l, m, acc):
        # ls: (N,), pesi_l: (3,N) ; tutti i punti della fenditura
        L = ls[:, None, None]
        SX = sx[None, :, None]
        SW = (sws[None, None, :] * SLIT_W * wloc[None, :, None])
        X, Y, ok = direzioni(L, np.broadcast_to(SX, (len(ls), ny, 4)), np.broadcast_to(SW, (len(ls), ny, 4)), m)
        wgt = (wloc[None, :, None] * np.ones_like(X)) * ok
        X = X - x0; Y = Y - y0
        sel = ok & (X > 1) & (X < acc.shape[2] - 2) & (Y > 1) & (Y < acc.shape[1] - 2)
        if not sel.any(): return
        ix = np.floor(X[sel]).astype(int); iy = np.floor(Y[sel]).astype(int)
        fx = (X[sel] - ix).astype(np.float32); fy = (Y[sel] - iy).astype(np.float32)
        lidx = np.broadcast_to(np.arange(len(ls))[:, None, None], X.shape)[sel]
        base = wgt[sel]
        Hc, Wc = acc.shape[1], acc.shape[2]
        for c in range(3):
            v = base * pesi_l[c][lidx]
            for dx, dy, ww in [(0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)]:
                acc[c] += np.bincount((iy + dy) * Wc + ix + dx, weights=v * ww, minlength=Hc * Wc).reshape(Hc, Wc).astype(np.float32)

    for b0 in bande:
        acc = np.zeros_like(img)
        sel = (l_c >= b0) & (l_c < b0 + 15)
        lc = l_c[sel]
        if len(lc) == 0: continue
        for m in (1, 2):
            pes = Q[:, sel] * cont[sel] * efficienza(lc, m) * 0.2
            deposita(lc, pes, m, acc)
            for lr, a in righe:
                if b0 <= lr < b0 + 15:
                    pl = qe(np.array([lr]))[:, :1] * a * efficienza(lr, m)
                    deposita(np.array([lr]), pl, m, acc)
        lm = b0 + 7.5
        s = sigma_px(lm)
        for c in range(3):
            acc[c] = gaussian_filter(acc[c], s)
        img += acc
    # luce diffusa dal DVD e dalle pareti: alone stretto + pedestallo largo
    for c in range(3):
        img[c] += 0.020 * gaussian_filter(img[c], (25, 45)) + 0.006 * gaussian_filter(img[c], 220)
    return img, (x0, x1, y0, y1)


def isp(img_crop, box, rng, esposizione=0.88):
    """Sensore + ISP iPhone semplificato. Restituisce immagine sRGB 8 bit e grezzo lineare."""
    x0, x1, y0, y1 = box
    full = np.zeros((3, H, W), np.float32)
    full[:, y0:y1, x0:x1] = img_crop
    # mosaico Bayer RGGB
    mask = np.zeros((3, H, W), bool)
    mask[0, 0::2, 0::2] = True; mask[1, 0::2, 1::2] = True; mask[1, 1::2, 0::2] = True; mask[2, 1::2, 1::2] = True
    raw = (full * mask).sum(0)
    raw = raw / raw.max() * esposizione * FULL_WELL                  # esposizione manuale
    raw = rng.poisson(np.clip(raw, 0, None) + 3.0).astype(np.float32) - 3.0  # shot + corrente di buio
    raw += rng.normal(0, READ_E, raw.shape).astype(np.float32)
    raw = np.clip(raw, 0, FULL_WELL) / FULL_WELL
    # demosaicizzazione bilineare
    k_g = np.array([[0, 1, 0], [1, 4, 1], [0, 1, 0]], np.float32) / 4
    k_rb = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], np.float32) / 4
    rgb = np.stack([convolve(raw * mask[0], k_rb), convolve(raw * mask[1], k_g), convolve(raw * mask[2], k_rb)], -1)
    rgb *= np.array([1.95, 1.0, 1.55], np.float32)                  # bilanciamento "luce diurna"
    ccm = np.array([[1.62, -0.45, -0.17], [-0.28, 1.52, -0.24], [0.02, -0.55, 1.53]], np.float32)
    rgb = np.clip(rgb @ ccm.T, 0, None)
    rgb = rgb / max(np.percentile(rgb, 99.995), 1e-6)
    blur = np.stack([gaussian_filter(rgb[..., c], 1.0) for c in range(3)], -1)
    rgb = rgb + 0.5 * (rgb - blur)                                     # nitidezza dell'ISP
    rgb = np.clip(rgb, 0, 1)
    srgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - 0.055)
    srgb = srgb - 0.06 * np.sin(2 * math.pi * srgb) / (2 * math.pi)     # leggera curva a S
    return (np.clip(srgb, 0, 1) * 255 + 0.5).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=".")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(11)
    for nome, src in [("cfl", sorgente_cfl), ("cielo", None), ("led", sorgente_led)]:
        img, box = renderizza(src, rng, nome)
        out = isp(img, box, rng)
        p = os.path.join(a.out, f"iphone11_{nome}.jpg")
        Image.fromarray(out).save(p, quality=90, subsampling=0)
        print("salvato", p)
    for l in (404.66, 435.83, 546.07, 611.6, 700):
        X, Y, _ = direzioni(np.array(l), np.array(0.0), np.array(0.0), 1)
        print(f"  λ={l:7.2f} nm -> x = {float(X):7.1f} px   σ_sfocatura = {sigma_px(l):.2f} px")


if __name__ == "__main__":
    main()
