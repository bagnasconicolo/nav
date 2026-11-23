# Scatoline aperte per minerali (PETG-CF)

Scatole senza coperchio su griglia da 25 mm: formati diversi si affiancano senza spazi nel cassetto
(misura esterna = n × 25 − 0,5 mm di gioco).

| File | Esterno (mm) | Uso tipico |
|---|---|---|
| 1x1 micromount | 24,5 × 24,5 × 16 | micromount |
| 2x1 micro-doppia | 49,5 × 24,5 × 18 | coppie / micro allungati |
| 2x2 thumbnail | 49,5 × 49,5 × 22 | thumbnail |
| 3x2 miniatura | 74,5 × 49,5 × 25 | miniature |
| 3x3 miniatura-grande | 74,5 × 74,5 × 28 | miniature grandi |
| 4x2 small-cabinet-rett | 99,5 × 49,5 × 25 | pezzi allungati |
| 4x4 small-cabinet | 99,5 × 99,5 × 32 | small cabinet |

Caratteristiche: parete 1,2 mm, fondo 1,2 mm, angoli raggiati, smusso interno 45° fondo/parete
(il campione si prende meglio e non si sporcano gli angoli), smusso esterno sul fondo contro l'elephant foot,
incavo frontale 0,3 mm per un'etichetta adesiva (alta 8 mm).

## Formati personalizzati
- `scatola_minerali.scad`: apri in OpenSCAD, cambia `celle_x`, `celle_y`, `altezza` (e il resto) dal Customizer.
- oppure aggiungi una riga a `FORMATI` in `genera_stl.py` e lancia `python3 genera_stl.py` (serve `pip install manifold3d trimesh`).

## Stampa in PETG-CF
- **Ugello temprato** (acciaio indurito/rubino): il carbonio consuma l'ottone. Pareti da 1,2 = 2 linee con ugello 0,6 o 3 linee con 0,4.
- Filamento **asciutto** (essicca 65 °C, 4–6 h): il PETG-CF assorbe umidità e fa fili.
- Ugello 240–260 °C, piatto 70–80 °C, ventola 30–50 %.
- Layer 0,2 mm (0,3 con ugello 0,6), perimetri quanti bastano a riempire la parete (2 con 0,6 – 3 con 0,4), 4 layer sotto, infill irrilevante (le pareti sono piene).
- Piatto PEI testurizzato consigliato; su PEI liscio usa colla stick come distaccante (il PETG ci si salda).
- Nessun supporto, stampa così com'è (aperta verso l'alto).
- Velocità moderata sui perimetri esterni (~60 mm/s) per una finitura opaca uniforme.
