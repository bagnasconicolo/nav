# Dime di foratura – Tavola periodica portatile (Padova)

Fonte: `pt_panel.dxf` (pannello plexi 2500 × 2000 mm, 236 fori Ø4.5 mm = 2 fori per cubo, interasse 40 mm, passo 125 mm).

## Pannelli in legno
- **2 pannelli rettangolari 1250 × 1250 mm** (un foglio 2500 × 1250 tagliato dritto a metà), multistrato 18 mm.
- Taglio dritto tra gruppo 9 e gruppo 10: **nessun cubo diviso**.
- Unica differenza rispetto al plexi: il blocco f (lantanidi/attinidi) è spostato di **60 mm a sinistra**,
  allineato sotto i gruppi 3–17 (La sotto Sc/Y, Eu|Gd sulla giunzione). Sul plexi era sfalsato e
  nessun taglio dritto lo avrebbe evitato.
- Pannello A (sinistro): 53 cubi, 106 fori. Pannello B (destro): 65 cubi, 130 fori.
- Prima riga di fori a 80 mm dal bordo alto. Riferimenti: **bordo ALTO + bordo di GIUNZIONE**.

## File
- `dima_pannello_A_sinistro.pdf`, `dima_pannello_B_destro.pdf` – pagina 1270 × 1270 mm, scala 1:1 (rotolo ≥ 1270 mm / 50")
- `quote_fori.csv` – coordinate di ogni foro (x dalla giunzione, y dal bordo alto)
- `genera_dime.py` – rigenera tutto: `python3 genera_dime.py pt_panel.dxf`
