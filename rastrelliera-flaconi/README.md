# Rastrelliera 5 flaconi (Ø40 × 70 mm) — Creality K2, PETG-CF

| File | Ingombro | Note |
|---|---|---|
| `rastrelliera_5_fila.stl` | 234 × 50 × 26 mm | 5 in fila, una tacca frontale per ogni flacone |
| `rastrelliera_5_sfalsata.stl` | 142 × 90 × 26 mm | 3 dietro + 2 davanti a 60°, più compatta e stabile |

Caratteristiche: fori Ø42 (gioco 1 mm per lato), tasca profonda 24 mm (~34% del flacone),
smusso d'invito sui fori, tacca frontale a U per afferrare il flacone e leggere l'etichetta,
foro Ø26 nel fondo per spingere fuori il flacone, angoli R8, smusso alla base contro la
"zampa d'elefante". Tutto è parametrico in `genera.py` (`pip install manifold3d trimesh`).

## Impostazioni consigliate (Creality Print, PETG-CF)
- Ugello **0,6 mm acciaio temprato** (va bene anche 0,4 temprato), layer 0,2–0,24 mm
- Ugello 250–260 °C, piatto 70–80 °C, ventola 20–40 %
- 3 perimetri, 4 strati sopra/sotto, infill gyroid 15–20 %
- Nessun supporto, nessun brim (al massimo un brim di 3 mm per la versione in fila)
- Asciugare il filamento (65 °C, 6–8 h) prima della stampa

Se i flaconi entrano troppo stretti/larghi, modifica `GIOCO` in `genera.py` e rigenera.

## Versione con scritte bicolore (CFS)
`rastrelliera_5_scritte_bicolore.3mf` (oppure i due STL `_BASE` + `_TESTO`): versione in fila
con un gradino frontale alto 12 mm su cui stanno le sigle **Li · Na · Cu · B · K**, incassate
di 0,6 mm (alte 7 mm, DejaVu Sans Bold) e riempite con il secondo colore.
234 × 62 × 26 mm, 163 cm³ pieni.

In Creality Print: apri il 3MF → quando chiede, carica come **un solo oggetto con più parti** →
assegna lo slot CFS del colore base alla parte `base` e un altro slot alla parte `scritte`.
Con layer 0,2 i cambi colore sono solo 3 layer (z 11,4–12), quindi poco spreco di spurgo.
Le sigle si cambiano nella lista `ETICHETTE` di `genera.py`.
