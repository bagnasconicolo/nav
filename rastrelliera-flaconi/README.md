# Rastrelliera 5 flaconi (Ø40 × 70 mm) — Creality K2, PETG-CF

| File | Ingombro | Note |
|---|---|---|
| `rastrelliera_5_fila.stl` | 237 × 57 × 30 mm | 5 in fila, una tacca frontale per ogni flacone |
| `rastrelliera_5_sfalsata.stl` | 145 × 93 × 30 mm | 3 dietro + 2 davanti a 60°, più compatta e stabile |

Caratteristiche: fori Ø41 (gioco 0,5 mm per lato), tasca profonda 27 mm (~40% del flacone),
smusso d'invito sui fori, tacca frontale a U per afferrare il flacone e leggere l'etichetta,
foro Ø14 nel fondo per spingere fuori il flacone, angoli R8, smusso alla base contro la
"zampa d'elefante". Tutto è parametrico in `genera.py` (`pip install manifold3d trimesh`).

## Impostazioni consigliate (Creality Print, PETG-CF)
- Ugello **0,6 mm acciaio temprato** (va bene anche 0,4 temprato), layer 0,2–0,24 mm
- Ugello 250–260 °C, piatto 70–80 °C, ventola 20–40 %
- 3 perimetri, 4 strati sopra/sotto, infill gyroid 15–20 %
- Nessun supporto, nessun brim (al massimo un brim di 3 mm per la versione in fila)
- Asciugare il filamento (65 °C, 6–8 h) prima della stampa

Se i flaconi entrano troppo stretti/larghi, modifica `GIOCO` in `genera.py` e rigenera.
