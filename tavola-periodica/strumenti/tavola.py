#!/usr/bin/env python3
"""Strumenti per la tavola periodica a cubi.

Comandi:
  genera                 rigenera elementi.scad da dati/elementi.csv
  elenco                 stampa posizione e incastri di ogni cubo
  esporta [Z ...|tutti]  esporta gli STL: di serie solo i campioni, "tutti" per l'intera tavola
  pannello               genera schema di foratura del pannello (SVG + CSV)

Il cubo vero e proprio sta in cubo_elemento.scad; qui ci sono solo i dati
e la logica "di tavola" (chi confina con chi).
"""
import csv
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(RADICE, "dati", "elementi.csv")
SCAD = os.path.join(RADICE, "cubo_elemento.scad")
SCAD_DATI = os.path.join(RADICE, "elementi.scad")
DIR_STL = os.path.join(RADICE, "stl")

GIOCO_PANNELLO = 0.5          # spazio tra un cubo e l'altro sul pannello

# Cubi "segnaposto" nella casella del gruppo 3, periodi 6 e 7
SEGNAPOSTO = [
    {"numero": "57–71", "simbolo": "La–Lu", "nome": "Lantanidi", "massa": "",
     "categoria": "lantanide", "riga": 6, "colonna": 3, "id": "segnaposto_lantanidi", "codice": 119},
    {"numero": "89–103", "simbolo": "Ac–Lr", "nome": "Attinidi", "massa": "",
     "categoria": "attinide", "riga": 7, "colonna": 3, "id": "segnaposto_attinidi", "codice": 120},
]

# Cubi esportati di serie: un campione per tipo di caso (bordi, nomi lunghi, segnaposto)
CAMPIONI = ["1", "2", "26", "79", "104", "segnaposto_lantanidi"]

# Marker ArUco sul fronte, per il riconoscimento con la fotocamera.
# ID del marker = numero atomico; 119 e 120 per i due segnaposto.
DIZIONARIO_ARUCO = "DICT_4X4_250"


def posizione(z):
    """(riga, colonna) nella tavola: righe 1-7 periodi, 8 vuota, 9-10 blocco f."""
    if 57 <= z <= 71:
        return 9, z - 57 + 3
    if 89 <= z <= 103:
        return 10, z - 89 + 3
    if z == 1:
        return 1, 1
    if z == 2:
        return 1, 18
    inizi = [(3, 2), (11, 3), (19, 4), (37, 5), (55, 6), (87, 7)]
    inizio, periodo = max(p for p in inizi if p[0] <= z)
    i = z - inizio
    if periodo in (2, 3):
        return periodo, i + 1 if i < 2 else i + 11
    if periodo in (4, 5):
        return periodo, i + 1
    # periodi 6 e 7: dopo i due del blocco s si salta il blocco f
    return periodo, i + 1 if i < 2 else i - 13


def carica():
    with open(CSV, newline="", encoding="utf-8") as f:
        el = list(csv.DictReader(f))
    for e in el:
        e["riga"], e["colonna"] = posizione(int(e["numero"]))
        e["id"] = f"{int(e['numero']):03d}_{e['simbolo']}"
    return el


def tutti_i_cubi():
    return carica() + SEGNAPOSTO


def con_vicini(cubi):
    occupate = {(c["riga"], c["colonna"]) for c in cubi}
    for c in cubi:
        r, k = c["riga"], c["colonna"]
        c["lingua_sopra"] = (r - 1, k) in occupate
        c["scanalatura_sotto"] = (r + 1, k) in occupate
        c["vicino_dx"] = (r, k + 1) in occupate
    return cubi


def scad_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def genera():
    righe = ["// GENERATO da strumenti/tavola.py genera - non modificare a mano.",
             "// [numero, simbolo, nome, massa, categoria, riga, colonna]",
             "ELEMENTI = ["]
    for e in carica():
        righe.append("  [{}, {}, {}, {}, {}, {}, {}],".format(
            e["numero"], scad_str(e["simbolo"]), scad_str(e["nome"]),
            scad_str(e["massa"]), scad_str(e["categoria"]), e["riga"], e["colonna"]))
    righe.append("];")
    # bit dei marker ArUco 6x6 (bordo compreso), riga per riga dall'alto: 0 = nero
    import cv2
    diz = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, DIZIONARIO_ARUCO))
    righe.append(f"// marker ArUco {DIZIONARIO_ARUCO}, indice = ID (0..120)")
    righe.append("ARUCO = [")
    for i in range(121):
        bit = (cv2.aruco.generateImageMarker(diz, i, 6) > 0).astype(int).flatten()
        righe.append("  [" + ",".join(map(str, bit)) + "],")
    righe.append("];")
    with open(SCAD_DATI, "w", encoding="utf-8") as f:
        f.write("\n".join(righe) + "\n")
    print("scritto", SCAD_DATI)


def elenco():
    for c in con_vicini(tutti_i_cubi()):
        print(f"{c['id']:<22} r{c['riga']:>2} c{c['colonna']:>2}  "
              f"su:{int(c['lingua_sopra'])} giu:{int(c['scanalatura_sotto'])}  {c['nome']}")


def b(v):
    return "true" if v else "false"


def comando_openscad(c, parte="corpo", uscita=None):
    uscita = uscita or os.path.join(DIR_STL, c["id"] + ".stl")
    d = {
        "parte": scad_str(parte),
        "lingua_sopra": b(c["lingua_sopra"]),
        "scanalatura_sotto": b(c["scanalatura_sotto"]),
        "finestra_sopra": b(c["lingua_sopra"]),
        "finestra_dx": b(c["vicino_dx"]),
    }
    if str(c["numero"]).isdigit():
        d["Z"] = c["numero"]
    else:
        d["Z"] = "0"
        d["numero_testo"] = scad_str(c["numero"])
        d["simbolo_testo"] = scad_str(c["simbolo"])
        d["nome_testo"] = scad_str(c["nome"])
        d["codice_id"] = str(c["codice"])
    cmd = ["openscad", "-o", uscita]
    for k, v in d.items():
        cmd += ["-D", f"{k}={v}"]
    return cmd + [SCAD]


def binario(percorso):
    """OpenSCAD 2021 scrive STL testuali: se c'è trimesh li converte in binario (~5x più piccoli)."""
    try:
        import trimesh
    except ImportError:
        return
    trimesh.load(percorso).export(percorso)


def esporta(numeri):
    os.makedirs(DIR_STL, exist_ok=True)
    cubi = con_vicini(tutti_i_cubi())
    if numeri != ["tutti"]:
        numeri = numeri or CAMPIONI
        cubi = [c for c in cubi if c["numero"] in numeri or c["simbolo"] in numeri
                or c["id"] in numeri]

    def uno(c):
        r = subprocess.run(comando_openscad(c), capture_output=True, text=True)
        stato = "ok" if r.returncode == 0 else "ERRORE\n" + r.stderr[-800:]
        if r.returncode == 0:
            binario(os.path.join(DIR_STL, c["id"] + ".stl"))
        print(c["id"], stato, flush=True)

    with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        list(ex.map(uno, cubi))
    # parti comuni, uguali per tutti i cubi
    for parte in ("tappo", "dima"):
        out = os.path.join(DIR_STL, f"comune_{parte}.stl")
        subprocess.run(["openscad", "-o", out, "-D", f'parte="{parte}"', SCAD], check=True)
        binario(out)
        print(out)


# Colore della cornice frontale per categoria (filamento del 2° colore)
COLORI_CORNICE = {
    "metallo-alcalino": "#d9534f", "metallo-alcalino-terroso": "#e8913a",
    "metallo-di-transizione": "#e3b23c", "metallo-post-transizione": "#7fae5b",
    "semimetallo": "#3fa597", "non-metallo": "#3d7cc9", "alogeno": "#7a5cc7",
    "gas-nobile": "#c45ab3", "lantanide": "#d4708f", "attinide": "#9c6b4e",
}



def quote_dal_modello():
    """Legge lato e posizione della vite direttamente da cubo_elemento.scad."""
    import re
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "info.echo")
        subprocess.run(["openscad", "-o", out, "-D", 'parte="info"', SCAD],
                       check=True, capture_output=True)
        testo = open(out).read()
    def coppia(nome):
        return tuple(map(float, re.search(nome + r" = \[([\d.]+), ([\d.]+)\]", testo).groups()))

    def num(nome):
        return float(re.search(nome + r" = ([\d.]+)", testo).group(1))
    return {"lato": num("LATO"), "profondita": num("PROFONDITA"), "cornice": num("CORNICE"),
            "vite": coppia("VITE"), "spina": coppia("SPINA"),
            "tappo": tuple(map(float, re.search(r"TAPPO = \[([\d.]+), ([\d.]+), ([\d.]+)\]", testo).groups()))}


def pannello():
    """Schema del pannello visto DI FRONTE (come lo guardi appeso al muro).
    Origine in basso a sinistra del primo cubo; coordinate in mm."""
    q = quote_dal_modello()
    LATO = q["lato"]
    # (nome, x, z, diametro consigliato) rispetto all'angolo basso-sinistro del cubo
    tipi = [("vite M4 - foro per inserto filettato", *q["vite"], 6),
            ("spina Ø6", *q["spina"], 6)]
    cubi = con_vicini(tutti_i_cubi())
    passo = LATO + GIOCO_PANNELLO
    righe_tot = max(c["riga"] for c in cubi)
    colonne_tot = max(c["colonna"] for c in cubi)
    W, H = colonne_tot * passo, righe_tot * passo
    fori = []
    for c in cubi:
        x0 = (c["colonna"] - 1) * passo
        z0 = (righe_tot - c["riga"]) * passo
        for nome, x, z, dia in tipi:
            fori.append((c["id"], nome, x0 + x, z0 + z, dia))
    with open(os.path.join(RADICE, "dati", "fori_pannello.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cubo", "foro", "x_mm_da_sinistra", "y_mm_dal_basso", "diametro_mm"])
        for r in fori:
            w.writerow([r[0], r[1], f"{r[2]:.1f}", f"{r[3]:.1f}", r[4]])
    m = 40
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W + 2*m}mm" height="{H + 2*m}mm" '
         f'viewBox="{-m} {-m} {W + 2*m} {H + 2*m}" font-family="Syne, IBM Plex Mono, sans-serif">',
         f'<rect x="{-m}" y="{-m}" width="{W + 2*m}" height="{H + 2*m}" fill="white"/>']
    for c in cubi:
        x = (c["colonna"] - 1) * passo
        y = (c["riga"] - 1) * passo
        s.append(f'<rect x="{x}" y="{y}" width="{LATO}" height="{LATO}" '
                 f'fill="{COLORI_CORNICE.get(c["categoria"], "#ddd")}" fill-opacity="0.35" '
                 f'stroke="#333" stroke-width="0.6"/>')
        s.append(f'<text x="{x + 6}" y="{y + 16}" font-size="10">{c["numero"]}</text>')
        s.append(f'<text x="{x + LATO/2}" y="{y + 55}" font-size="28" font-weight="700" '
                 f'text-anchor="middle">{c["simbolo"]}</text>')
        s.append(f'<text x="{x + LATO/2}" y="{y + 72}" font-size="9" '
                 f'text-anchor="middle">{c["nome"]}</text>')
        for _, xf, zf, d in tipi:
            s.append(f'<circle cx="{x + xf}" cy="{y + LATO - zf}" r="{d/2}" '
                     f'fill="none" stroke="#c00" stroke-width="0.6"/>')
    s.append(f'<text x="0" y="{H + 25}" font-size="14">Pannello {W:.0f} × {H:.0f} mm — '
             f'passo {passo} mm — in rosso i fori: vite (centro) e spina. '
             f'Quote esatte in dati/fori_pannello.csv</text>')
    s.append("</svg>")
    with open(os.path.join(RADICE, "dati", "pannello.svg"), "w", encoding="utf-8") as f:
        f.write("\n".join(s))
    print(f"pannello {W:.0f} x {H:.0f} mm, {len(cubi)} cubi, {len(fori)} fori")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "esporta":
        esporta(args)
    else:
        {"genera": genera, "elenco": elenco, "pannello": pannello}[cmd]()
