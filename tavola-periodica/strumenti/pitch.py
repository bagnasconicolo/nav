#!/usr/bin/env python3
"""Immagini per presentazioni: render Blender + tavola con le didascalie.

uso: python3 strumenti/pitch.py [tavola] [dettaglio] [fronte] [esploso]   (di serie: tutte)

Prima serve "python3 strumenti/tavola.py esporta tutti" per la tavola completa.
Le immagini finiscono in anteprime/pitch_*.png.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tavola  # noqa: E402

RADICE = tavola.RADICE
TMP = os.environ.get("RENDER_TMP", "/tmp/render_tavola")
USCITA = os.path.join(RADICE, "anteprime")
BLENDER = os.path.join(RADICE, "strumenti", "render_blender.py")
FONT = os.path.join(RADICE, "font")

# l'oro: in tavola ha un cubo sopra (Ag) e uno a destra (Hg), quindi mostra
# linguetta e finestre come sono davvero
ESEMPIO = "79"


def blender(*argomenti):
    env = dict(os.environ, RENDER_TMP=TMP)
    r = subprocess.run(["blender", "-b", "-P", BLENDER, "--", *argomenti],
                       capture_output=True, text=True, env=env)
    if "Saved:" not in r.stdout:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit("render non riuscito")


def prepara_esploso():
    os.makedirs(TMP, exist_ok=True)
    c = next(c for c in tavola.con_vicini(tavola.tutti_i_cubi()) if c["numero"] == ESEMPIO)
    cubo = os.path.join(TMP, "cubo.stl")
    subprocess.run(tavola.comando_openscad(c, "corpo_appeso", cubo), check=True, capture_output=True)
    tappo = os.path.join(TMP, "tappo.stl")
    subprocess.run(["openscad", "-o", tappo, "-D", 'parte="tappo"', tavola.SCAD], check=True, capture_output=True)
    with open(os.path.join(TMP, "pezzi.json"), "w") as f:
        json.dump({"cubo": cubo, "tappo": tappo}, f)


# ---------------------------------------------------------------------------
# Didascalie
# ---------------------------------------------------------------------------
# chiave del punto: (titolo, testo). Il lato e l'altezza dell'etichetta si
# decidono da soli, in base a dove cade il punto nell'immagine.
DIDASCALIE_ESPLOSO = {
    "fuga": ("Spigoli raggiati", "tra quattro cubi resta\nuna fuga a rombo"),
    "linguetta": ("Linguetta", "coda di rondine a 45°:\ni cubi si sfilano in avanti"),
    "finestra_sopra": ("Finestre", "solo verso un vicino (sopra\ne a destra): −10% di materiale"),
    "tappo": ("Tappino", "copre la vite, a filo"),
    "vite": ("Vite M3 svasata", "una sola, al centro"),
    "spina": ("Spina Ø4", "nello stesso mozzo:\nil cubo non ruota"),
    "inserto": ("Inserto filettato M3", "nel pannello: il cubo\nsi toglie e si rimette"),
    "pannello": ("Pannello", "multistrato 18 mm"),
}
DIDASCALIE_FRONTE = {
    "simbolo": ("Simbolo", "Syne Bold, 6 mm"),
    "numero": ("Numero atomico", "IBM Plex Mono, 4,5 mm"),
    "marker": ("Marker ArUco", "ID = numero atomico:\nl'app riconosce il cubo\ncon la fotocamera"),
    "fronte": ("Fronte chiaro", "cambio filamento a 58 mm;\ntesti e marker a 60 mm"),
    "nicchia": ("Nicchia ad alcova", "raccordata su tutti i lati,\nsenza spigoli"),
    "tappo": ("Tappino", "nasconde l'unica vite"),
}


def disponi(voci, alto, basso):
    """Altezze delle etichette di una colonna: vicine al loro punto, mai sovrapposte.
    voci: (chiave, y del punto, righe di testo)."""
    voci = sorted(voci, key=lambda v: v[1])
    passo = [70 + 23 * v[2] for v in voci]
    ys = []
    for i, (_, y, _) in enumerate(voci):
        ys.append(max(y, ys[-1] + passo[i - 1]) if ys else max(y, alto))
    eccesso = ys[-1] - basso if ys else 0
    if eccesso > 0:   # se si sfora in basso, risale tutto quanto serve
        ys = [y - eccesso for y in ys]
        for i in range(len(ys) - 2, -1, -1):
            ys[i] = min(ys[i], ys[i + 1] - passo[i])
    return [(v[0], y) for v, y in zip(voci, ys)]


def componi(render, punti, didascalie, titolo, sottotitolo, uscita):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.patheffects as pe
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm

    syne = fm.FontProperties(fname=os.path.join(FONT, "Syne-Bold.ttf"))
    mono = fm.FontProperties(fname=os.path.join(FONT, "IBMPlexMono-Medium.ttf"))
    sans = fm.FontProperties(fname=os.path.join(FONT, "IBMPlexSans-Medium.ttf"))
    img = plt.imread(render)
    H, W = img.shape[:2]
    with open(punti) as f:
        pt = json.load(f)

    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img)
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    chiaro, tenue, fondo = "#ece8e1", "#9a968f", "#111113"
    alone = [pe.withStroke(linewidth=5, foreground=fondo)]   # leggibile anche sopra gli oggetti
    ax.text(70, 120, titolo, fontproperties=syne, fontsize=54, color=chiaro, va="baseline")
    ax.text(72, 175, sottotitolo, fontproperties=mono, fontsize=19, color=tenue, va="baseline")

    meta = W * 0.5
    voci = {k: (k, pt[k][1], testo.count("\n") + 1) for k, (_, testo) in didascalie.items()}
    for lato in ("sx", "dx"):
        colonna = [v for k, v in voci.items() if (pt[k][0] < meta) == (lato == "sx")]
        for chiave, ly in disponi(colonna, 290, H - 150):
            tit, testo = didascalie[chiave]
            x, y = pt[chiave]
            lx = 70 if lato == "sx" else W - 70
            gomito = lx + (430 if lato == "sx" else -430)
            ax.plot([x, gomito, lx], [y, ly, ly], color=chiaro, lw=1.1, alpha=0.8, solid_capstyle="round")
            ax.plot([x], [y], "o", ms=7, mfc=chiaro, mec="#111", mew=1.5)
            ha = "left" if lato == "sx" else "right"
            ax.text(lx, ly - 12, tit, fontproperties=sans, fontsize=21, color=chiaro, ha=ha, va="bottom",
                    path_effects=alone)
            ax.text(lx, ly + 10, testo, fontproperties=mono, fontsize=14, color=tenue, ha=ha, va="top",
                    linespacing=1.35, path_effects=alone)
    fig.savefig(uscita, dpi=100, facecolor="#0b0b0c")
    plt.close(fig)


SOTTOTITOLO = "60 × 60 × 60 mm  ·  PLA  ·  ~35 g  ·  stampato senza supporti"


def main(cosa):
    os.makedirs(USCITA, exist_ok=True)
    if "tavola" in cosa:
        blender("tavola", os.path.join(USCITA, "pitch_tavola.png"))
        print("pitch_tavola.png")
    if "dettaglio" in cosa:
        blender("tavola", os.path.join(USCITA, "pitch_dettaglio.png"), "dettaglio")
        print("pitch_dettaglio.png")
    if "esploso" in cosa or "fronte" in cosa:
        prepara_esploso()
    for scena, didascalie, titolo in (("esploso", DIDASCALIE_ESPLOSO, "Montaggio"),
                                      ("fronte", DIDASCALIE_FRONTE, "Anatomia del cubo")):
        if scena in cosa:
            grezzo = os.path.join(TMP, scena + ".png")
            punti = os.path.join(TMP, scena + ".json")
            blender(scena, grezzo, punti)
            componi(grezzo, punti, didascalie, titolo, SOTTOTITOLO,
                    os.path.join(USCITA, f"pitch_{scena}.png"))
            print(f"pitch_{scena}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or ["tavola", "dettaglio", "fronte", "esploso"])
