# Portachiavi "montagna" per Natz (stampa 3D)

Portachiavi da muro a forma di montagna con fessure "da arrampicata": ogni chiave
è appesa a un **nut** colorato che si infila dal basso nella fessura, sale e si
incastra nella strettoia, come un nut vero in una fessura di roccia.

![anteprima](anteprima.png)

## File

| File | Cosa |
|---|---|
| `portachiavi.scad` | modello parametrico OpenSCAD (tutte le misure nel Customizer) |
| `stl/base.stl` | la montagna, 160 × 135 × 15 mm, 3 fessure |
| `stl/nut.stl` | un nut |
| `stl/nut_x3.stl` | 3 nut sul piatto (se li fai dello stesso colore) |

Rigenerare gli STL dopo una modifica:

```bash
openscad -D 'parte="base"' -o stl/base.stl portachiavi.scad
```

```bash
openscad -D 'parte="nut"' -o stl/nut.stl portachiavi.scad
```

## Stampa

Serve un piatto di almeno **165 × 140 mm**: ci sta su qualsiasi stampante,
anche sull'A1 mini.

- **Base**: PLA effetto legno (o PLA marrone), stampata **col retro sul piatto**
  così com'è nello STL. Nessun supporto: le fessure sono aperte verso l'alto e le
  tasche delle viti sono ponti da 14 mm. Layer 0.2 mm, 3 perimetri, infill 15 %.
  Bello anche con cambio filamento a 3 mm: il fondo delle fessure viene più
  scuro, come nell'originale. Il raccordo del bordo frontale è fatto a gradini
  da 0.3 mm: con layer da 0.2-0.3 mm non si vedono.
- **Nut**: 3 colori (giallo, rosso, azzurro), stampati in piedi con il lato
  stretto (con i fori) sul piatto. Nessun supporto. 100 % infill o 4 perimetri:
  sono piccoli e lavorano a compressione.

## Montaggio dei portachiavi

Per ogni nut:

1. Cavetto d'acciaio Ø 1.5 mm, ~20 cm (o cordino Ø 2 mm).
2. Infilalo dal basso in un foro, passa nella canalina in cima, ridiscendi
   dall'altro foro.
3. Infila l'anello portachiavi e chiudi il cappio con una ghiera da crimpare
   (per cavo 1.5 mm) + guaina termorestringente nera, come nella foto originale.
   Col cordino basta un nodo.

## Fissaggio a muro

Due asole a buco di serratura sul retro, interasse 77 mm: due viti con testa
Ø ≤ 9 mm (es. 4 × 30 + tassello), lasciate sporgere ~4 mm. Appoggia, abbassa, fatto.

## Uso

Infila il nut dal basso nella fessura (il lato largo verso l'alto), spingilo su:
si blocca da solo dove la fessura si stringe. Per toglierlo spingilo su di un
millimetro e tiralo giù.

Se il nut è troppo lasco o troppo duro (dipende dalla stampante), cambia
`strettoia` nel Customizer (default 11.5 mm: più piccolo = si ferma più in basso).
