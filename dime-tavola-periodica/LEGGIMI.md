# Dime di foratura – Tavola periodica portatile (Padova)

Fonte: `pt_panel.dxf` (pannello plexi 2500 × 2000 mm, 236 fori Ø4.5 mm = 2 fori per cubo, interasse 40 mm, passo 125 mm).

## Pannelli in legno
- **2 pannelli da 1250 × 1250 mm** (un foglio standard 2500 × 1250 tagliato a metà), multistrato 18 mm consigliato.
- La giunzione cade esattamente a metà del plexi, tra il gruppo 9 (Co/Rh/Ir/Mt) e il gruppo 10 (Ni/Pd/Pt/Ds).
- Eu e Am sono a cavallo della giunzione: un foro su ciascun pannello (22.5 / 17.5 mm dal bordo).
- Prima riga di fori a 65 mm dal bordo alto. Riferimenti: **bordo ALTO + bordo di GIUNZIONE**.

## File
- `dima_pannello_A_sinistro.pdf` – 104 fori
- `dima_pannello_B_destro.pdf` – 132 fori
- `quote_fori.csv` – distanze di ogni foro da giunzione e bordo alto (per controllo / tracciatura a mano)
- `genera_dime.py` – rigenera tutto: `python3 genera_dime.py pt_panel.dxf`

PDF in pagina 1270 × 1270 mm (rotolo 50"/1270 mm o più largo), stampa al 100 %.
