# Dime di foratura – Tavola periodica portatile (Padova)

Fonte: `pt_panel.dxf` (pannello plexi 2500 × 2000 mm, 236 fori Ø4.5 mm = 2 fori per cubo, interasse 40 mm, passo 125 mm).

## Pannelli in legno
- **Un foglio 2500 × 1250 mm** (multistrato 18 mm consigliato) diviso in 2 con un **taglio a gradino**, così nessun cubo resta a cavallo:
  - tratto alto (925 mm dal bordo superiore): a 1250 mm dal bordo sinistro, tra gruppo 9 e 10 (Co|Ni … Mt|Ds);
  - gradino orizzontale di 60 mm verso destra, nello spazio vuoto tra periodo 7 e lantanidi (925 mm dall'alto);
  - tratto basso (325 mm): a 1310 mm dal bordo sinistro, tra Eu|Gd e Am|Cm.
- Pannello A (sinistro): 1250 × 1250 con dente 60 × 325 in basso a destra → 53 cubi, 106 fori.
- Pannello B (destro): 1250 × 1250 con tacca 60 × 325 in basso a sinistra → 65 cubi, 130 fori.
- Prima riga di fori a 65 mm dal bordo alto. Riferimenti: **bordo ALTO + tratto alto della GIUNZIONE**.

## File
- `dima_pannello_A_sinistro.pdf` (pagina 1330 × 1270 mm)
- `dima_pannello_B_destro.pdf` (pagina 1270 × 1270 mm)
- `quote_fori.csv` – coordinate di ogni foro (x dalla giunzione alta, y dal bordo alto)
- `genera_dime.py` – rigenera tutto: `python3 genera_dime.py pt_panel.dxf`

Stampa su rotolo da 50"/1270 mm (o più largo), al 100 %. Il contorno della dima è anche la traccia del taglio a gradino.
