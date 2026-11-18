#!/usr/bin/env python3
"""
spettro.py — estrazione, calibrazione e misura di spettri dallo spettroscopio
per smartphone (reticolo DVD/CD in trasmissione, camera focheggiata a infinito).

  Calibrazione con lampada fluorescente compatta (CFL) o tubo al neon/Hg:
      python3 spettro.py calibra foto_cfl.jpg            -> calibrazione.json
  Misura:
      python3 spettro.py misura campione.jpg [--dark buio.jpg] [--ref bianco.jpg]
                                             -> campione_spettro.csv/.png
  Verifica con immagine sintetica (nessun hardware):
      python3 spettro.py demo

Modello fisico usato per l'identificazione automatica delle righe:
    reticolo parallelo al sensore, incidenza alpha = asin(lambda_c/d)
    sin(beta) = lambda/d - sin(alpha)          (equazione del reticolo, m = 1)
    x_pixel   = x0 + K * tan(beta)             (camera senza distorsione)
Poi un polinomio di grado 2-3 assorbe distorsione residua e passo reale del DVD.

Dipendenze: numpy, scipy, pillow, matplotlib (opz. rawpy per DNG).
"""
import argparse, itertools, json, math, os, sys
import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d, shift as nd_shift

# Righe di riferimento (nm, aria). Hg I da NIST ASD; fosfori CFL: Tb3+ e Eu3+ (Y2O3:Eu).
RIGHE_CFL = {
    404.656: "Hg", 435.833: "Hg", 487.7: "Tb", 542.4: "Tb", 546.074: "Hg",
    576.960: "Hg", 579.066: "Hg", 611.6: "Eu",
}
RIGHE_PRINCIPALI = [435.833, 546.074, 611.6]   # sempre presenti e intense nelle CFL
RIGHE_NEON = {585.249: "Ne", 588.190: "Ne", 594.483: "Ne", 607.434: "Ne", 609.616: "Ne",
              614.306: "Ne", 616.359: "Ne", 621.728: "Ne", 626.650: "Ne", 633.443: "Ne",
              638.299: "Ne", 640.225: "Ne", 650.653: "Ne", 659.895: "Ne", 703.241: "Ne"}


# ----------------------------------------------------------------------------- I/O
def carica(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".dng", ".nef", ".cr2", ".arw"):
        import rawpy  # lineare, senza curva gamma: preferibile per misure
        with rawpy.imread(path) as r:
            img = r.postprocess(gamma=(1, 1), no_auto_bright=True, output_bps=16,
                                use_camera_wb=False, user_wb=[1, 1, 1, 1])
        return img.astype(np.float64) / 65535.0, True
    from PIL import Image
    img = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64) / 255.0
    return img, False


def linearizza_srgb(c):
    """Inverte la curva sRGB dei JPEG (approssimazione: il telefono applica anche tone-mapping)."""
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# ---------------------------------------------------------------- estrazione profilo
def orienta(img, asse):
    """Restituisce l'immagine con la dispersione lungo le colonne (asse x)."""
    lum = img.mean(axis=2)
    if asse == "auto":
        # lungo la dispersione il profilo ha molte righe (variazione totale alta);
        # lungo la fenditura è un "gradino" liscio (variazione totale ~2)
        def tv(p):
            p = gaussian_filter1d(p, 2.0)
            return np.abs(np.diff(p)).sum() / (p.max() - p.min() + 1e-12)
        asse = "x" if tv(lum.sum(axis=0)) >= tv(lum.sum(axis=1)) else "y"
    return (img if asse == "x" else np.transpose(img, (1, 0, 2))), asse


def banda_righe(lum, frazione=0.5):
    """Righe dell'immagine occupate dall'immagine della fenditura."""
    prof = gaussian_filter1d(lum.sum(axis=1), 3)
    soglia = prof.min() + frazione * (prof.max() - prof.min())
    idx = np.where(prof > soglia)[0]
    r0, r1 = int(idx.min()), int(idx.max())
    m = max(1, (r1 - r0) // 10)            # scarta i bordi della fenditura
    return r0 + m, r1 - m


def stima_inclinazione(lum, r0, r1, n=8):
    """Pendenza (px/riga) delle righe spettrali: fenditura non perfettamente parallela."""
    edges = np.linspace(r0, r1, n + 1).astype(int)
    rif = gaussian_filter1d(lum[r0:r1].mean(axis=0), 1.5)
    rif = rif - rif.mean()
    cs, ys = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        p = gaussian_filter1d(lum[a:b].mean(axis=0), 1.5); p = p - p.mean()
        cc = np.correlate(p, rif, mode="full")
        k = int(np.argmax(cc))
        if 0 < k < len(cc) - 1:               # interpolazione parabolica sub-pixel
            y0, y1, y2 = cc[k - 1], cc[k], cc[k + 1]
            k = k + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)
        cs.append(k - (len(rif) - 1)); ys.append((a + b) / 2)
    return float(np.polyfit(ys, cs, 1)[0])


def profilo(img, r0, r1, pend, rc=None):
    """Somma le righe r0..r1 dopo aver raddrizzato l'inclinazione. Ritorna (N,3)."""
    rc = (r0 + r1) / 2 if rc is None else rc
    out = np.zeros((img.shape[1], 3))
    for r in range(r0, r1 + 1):
        s = -pend * (r - rc)
        out += nd_shift(img[r], (s, 0), order=1, mode="nearest")
    return out / (r1 - r0 + 1)


def picchi(y, prominenza=0.04):
    y = gaussian_filter1d(y, 1.0)
    pk, pr = find_peaks(y, prominence=prominenza * y.max(), distance=4)
    pos = []
    for p in pk:                            # centroide sub-pixel (parabola sul log)
        if 0 < p < len(y) - 1 and min(y[p - 1:p + 2]) > 0:
            l0, l1, l2 = np.log(y[p - 1:p + 2])
            den = l0 - 2 * l1 + l2
            pos.append(p + (0.5 * (l0 - l2) / den if den != 0 else 0))
        else:
            pos.append(float(p))
    return np.array(pos), pr["prominences"]


# ------------------------------------------------------------------- calibrazione
def modello_x(lam, K, x0, d, alpha):
    beta = np.arcsin(np.asarray(lam) / d - math.sin(alpha))
    return x0 + K * np.tan(beta)


def identifica(pos, prom, righe, d, lambda_c, tol_px=None):
    """Trova K, x0 tali che il modello fisico spieghi il maggior numero di picchi."""
    alpha = math.asin(lambda_c / d)
    ordine = np.argsort(prom)[::-1][:6]
    forti = pos[ordine]
    rif = np.array(sorted(righe))
    tb = np.tan(np.arcsin(rif / d - math.sin(alpha)))
    tol_px = tol_px or max(3.0, 0.004 * (pos.max() - pos.min() + 1))
    best = None
    for (i, j) in itertools.permutations(range(len(forti)), 2):
        for (a, b) in itertools.combinations(range(len(rif)), 2):
            K = (forti[j] - forti[i]) / (tb[b] - tb[a])
            if K == 0 or not np.isfinite(K):
                continue
            x0 = forti[i] - K * tb[a]
            pred = x0 + K * tb
            dist = np.abs(pos[:, None] - pred[None, :])
            usati, coppie = set(), []
            for k in np.argsort(dist.min(axis=0)):
                p = int(np.argmin(dist[:, k]))
                if dist[p, k] < tol_px and p not in usati:
                    usati.add(p); coppie.append((pos[p], rif[k]))
            score = len(coppie) - 1e-3 * sum(abs(c[0] - (x0 + K * np.tan(np.arcsin(c[1] / d - math.sin(alpha))))) for c in coppie)
            if best is None or score > best[0]:
                best = (score, K, x0, coppie)
    return best


def calibra(args):
    img, raw = carica(args.immagine)
    img, asse = orienta(img, args.asse)
    lum = img.mean(axis=2)
    r0, r1 = banda_righe(lum)
    pend = stima_inclinazione(lum, r0, r1)
    prof = profilo(img, r0, r1, pend).sum(axis=1)
    pos, prom = picchi(prof)
    righe = RIGHE_NEON if args.lampada == "neon" else RIGHE_CFL
    best = identifica(pos, prom, list(righe), args.passo, args.lambda_c)
    if best is None or len(best[3]) < 3:
        sys.exit("Calibrazione fallita: meno di 3 righe riconosciute. Controlla fuoco/esposizione.")
    _, K, x0, coppie = best
    coppie.sort()
    xs, ls = np.array([c[0] for c in coppie]), np.array([c[1] for c in coppie])
    grado = 3 if len(xs) >= 6 else (2 if len(xs) >= 4 else 1)
    coeff = np.polyfit(xs, ls, grado)
    res = ls - np.polyval(coeff, xs)
    dof = max(1, len(xs) - grado - 1)
    rms = float(np.sqrt((res ** 2).sum() / dof))
    disp = float(abs(np.polyval(np.polyder(coeff), np.mean(xs))))
    # risoluzione: FWHM della riga Hg 546.07 (o della più intensa)
    k546 = int(np.argmin(abs(ls - 546.074)))
    fwhm_nm = fwhm(prof, xs[k546]) * disp
    cal = dict(asse=asse, righe=[r0, r1], pendenza_px_per_riga=pend, polinomio=coeff.tolist(),
               grado=grado, rms_nm=rms, nm_per_px=disp, fwhm_nm=fwhm_nm, raw=raw,
               coppie=[[float(x), float(l)] for x, l in coppie],
               modello=dict(K_px=float(K), x0_px=float(x0), passo_nm=args.passo, lambda_c=args.lambda_c))
    with open(args.out, "w") as f:
        json.dump(cal, f, indent=2)
    print(f"Asse dispersione: {asse}   righe {r0}-{r1}   inclinazione {pend*1000:.2f} mpx/riga")
    print(f"Righe riconosciute ({len(xs)}):")
    for x, l, r in zip(xs, ls, res):
        print(f"   x = {x:8.2f} px   λ = {l:8.3f} nm   residuo {r:+.3f} nm   [{righe[l]}]")
    print(f"Polinomio grado {grado}: RMS = {rms:.3f} nm,  dispersione = {disp:.4f} nm/px")
    print(f"FWHM riga 546 nm ≈ {fwhm_nm:.2f} nm   ->  calibrazione salvata in {args.out}")
    if args.grafico:
        grafico(np.polyval(coeff, np.arange(len(prof))), prof / prof.max(), args.grafico,
                titolo=f"Calibrazione — RMS {rms:.3f} nm, FWHM {fwhm_nm:.2f} nm", marcatori=ls)
    return cal


def fwhm(y, x):
    y = gaussian_filter1d(y, 0.7); i = int(round(x))
    lo, hi = max(0, i - 40), min(len(y), i + 40)
    seg = y[lo:hi]; base = np.percentile(seg, 10); top = y[i] - base
    half = base + top / 2
    l = i
    while l > lo and y[l] > half: l -= 1
    r = i
    while r < hi - 1 and y[r] > half: r += 1
    # interpolazione lineare dei bordi
    xl = l + (half - y[l]) / (y[l + 1] - y[l] + 1e-12)
    xr = r - 1 + (half - y[r - 1]) / (y[r] - y[r - 1] - 1e-12)
    return float(xr - xl)


# ---------------------------------------------------------------------- misura
def misura(args):
    cal = json.load(open(args.cal))
    def prof_di(path):
        img, raw = carica(path)
        img, _ = orienta(img, cal["asse"])
        if not raw and not args.no_linear:
            img = linearizza_srgb(img)
        r0, r1 = cal["righe"]
        return profilo(img, r0, r1, cal["pendenza_px_per_riga"])
    p = prof_di(args.immagine)
    if args.dark: p = p - prof_di(args.dark)
    lam = np.polyval(cal["polinomio"], np.arange(len(p)))
    o = np.argsort(lam)                       # ordina per lunghezza d'onda crescente
    lam, p = lam[o], p[o]
    sel = (lam >= args.min) & (lam <= args.max)
    tot = p.sum(axis=1)
    if args.ref:
        r = prof_di(args.ref)
        if args.dark: r = r - prof_di(args.dark)
        rt = r[o].sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            T = np.clip(tot / rt, 0, 2)
            A = -np.log10(np.clip(T, 1e-4, None))
        out = np.c_[lam[sel], tot[sel], rt[sel], T[sel], A[sel]]
        hdr = "lambda_nm,campione,riferimento,trasmittanza,assorbanza"
    else:
        out = np.c_[lam[sel], tot[sel], p[sel]]
        hdr = "lambda_nm,intensita,R,G,B"
    base = os.path.splitext(args.immagine)[0] + "_spettro"
    np.savetxt(base + ".csv", out, delimiter=",", header=hdr, comments="", fmt="%.6g")
    y = out[:, 3] if args.ref else out[:, 1] / out[:, 1].max()
    grafico(out[:, 0], y, base + ".png", titolo=os.path.basename(args.immagine),
            ylabel="Trasmittanza" if args.ref else "Intensità relativa")
    print(f"Salvati {base}.csv e {base}.png  ({sel.sum()} punti, {args.min:g}-{args.max:g} nm)")


# -------------------------------------------------------------------- grafico
def lambda_rgb(l):
    if l < 380 or l > 780: return (0.5, 0.5, 0.5)
    if l < 440: r, g, b = (440 - l) / 60, 0, 1
    elif l < 490: r, g, b = 0, (l - 440) / 50, 1
    elif l < 510: r, g, b = 0, 1, (510 - l) / 20
    elif l < 580: r, g, b = (l - 510) / 70, 1, 0
    elif l < 645: r, g, b = 1, (645 - l) / 65, 0
    else: r, g, b = 1, 0, 0
    f = 0.3 + 0.7 * (l - 380) / 40 if l < 420 else (0.3 + 0.7 * (780 - l) / 80 if l > 700 else 1)
    return (r * f, g * f, b * f)


def grafico(x, y, path, titolo="", ylabel="Intensità relativa", marcatori=()):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sel = (x > 360) & (x < 800)
    fig, ax = plt.subplots(figsize=(9, 3.6), dpi=150)
    for i in np.where(sel)[0][:-1]:
        ax.fill_between(x[i:i + 2], 0, y[i:i + 2], color=lambda_rgb(x[i]), lw=0)
    ax.plot(x[sel], y[sel], color="#222", lw=0.8)
    for m in marcatori:
        ax.axvline(m, color="#888", lw=0.5, ls=":")
    ax.set_xlim(380, 750); ax.set_ylim(0, None)
    ax.set_xlabel("λ (nm)"); ax.set_ylabel(ylabel); ax.set_title(titolo, fontsize=10)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


# ------------------------------------------------------------------------ demo
def demo(args):
    """Genera una foto sintetica di CFL con lo strumento reale e verifica la calibrazione."""
    from PIL import Image
    d, lc = args.passo, args.lambda_c
    f_cam, pix = 5.7, 1.0e-3            # mm: focale e pixel tipici di camera principale 12 MP
    f_col, slit = 45.0, 0.05            # collimatore e fenditura 50 µm
    alpha = math.asin(lc / d)
    W, H = 4032, 3024
    K = f_cam / pix                     # px per unità di tan(beta)
    larg = slit * f_cam / f_col * math.cos(alpha) / pix   # larghezza immagine fenditura (px)
    sig = max(0.6, larg / 2.355)
    rng = np.random.default_rng(1)
    intens = {404.656: .25, 435.833: .8, 487.7: .35, 542.4: .3, 546.074: 1.0,
              576.960: .25, 579.066: .25, 611.6: .9, 587.6: .08, 631: .12, 707: .06}
    x = np.arange(W)
    riga = np.zeros((W, 3))
    for l, a in intens.items():
        xc = W / 2 + K * math.tan(math.asin(l / d - math.sin(alpha)))
        riga += a * np.exp(-0.5 * ((x - xc) / sig) ** 2)[:, None] * np.array(lambda_rgb(l))
    riga += 0.03 * np.exp(-0.5 * ((x - W / 2) / 900) ** 2)[:, None]   # continuo dei fosfori
    img = np.zeros((H, W, 3))
    pend = math.tan(math.radians(0.8))                               # fenditura ruotata 0.8°
    for r in range(H // 2 - 330, H // 2 + 330):
        img[r] = nd_shift(riga, (pend * (r - H / 2), 0), order=1)
    img = np.clip(img / img.max() * 0.9 + rng.normal(0, 0.01, img.shape), 0, 1)
    path = os.path.join(args.cartella, "demo_cfl.png")
    Image.fromarray((img * 255).astype(np.uint8)).save(path)
    print(f"Immagine sintetica: {path}  (fenditura 50 µm -> {larg:.1f} px, inclinazione 0.8°)")
    ns = argparse.Namespace(immagine=path, asse="auto", lampada="cfl", passo=d, lambda_c=lc,
                            out=os.path.join(args.cartella, "demo_calibrazione.json"),
                            grafico=os.path.join(args.cartella, "demo_calibrazione.png"))
    calibra(ns)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--passo", type=float, default=740.0, help="passo reticolo nm (DVD 740, CD 1600)")
    ap.add_argument("--lambda-c", dest="lambda_c", type=float, default=550.0)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("calibra"); c.add_argument("immagine")
    c.add_argument("--lampada", choices=["cfl", "neon"], default="cfl")
    c.add_argument("--asse", choices=["auto", "x", "y"], default="auto")
    c.add_argument("--out", default="calibrazione.json")
    c.add_argument("--grafico", default="calibrazione.png")
    m = sub.add_parser("misura"); m.add_argument("immagine")
    m.add_argument("--cal", default="calibrazione.json")
    m.add_argument("--dark"); m.add_argument("--ref")
    m.add_argument("--min", type=float, default=380); m.add_argument("--max", type=float, default=750)
    m.add_argument("--no-linear", action="store_true", help="non invertire la gamma sRGB")
    dm = sub.add_parser("demo"); dm.add_argument("--cartella", default=".")
    a = ap.parse_args()
    {"calibra": calibra, "misura": misura, "demo": demo}[a.cmd](a)


if __name__ == "__main__":
    main()
