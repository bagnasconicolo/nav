# Cervino / Matterhorn – STL per stampa 3D

Modelli generati da dati altimetrici reali: **Copernicus DEM GLO-30** (ESA, 30 m),
tile N45E007 + N46E007, riproiettate in UTM 32N e centrate sulla vetta (45.9763 N, 7.6586 E).

| File | Area reale | Dimensioni | Scala |
|---|---|---|---|
| `cervino_4km_180mm.stl` | 4 × 4 km | 180 × 180 × 90 mm | 1:22.222 |
| `cervino_6km_180mm.stl` | 6 × 6 km | 180 × 180 × 70 mm | 1:33.333 |

Nord = asse +Y. Mesh chiusa (watertight), base piena di 5 mm sotto il punto più basso.

Nota: a 30 m di risoluzione la punta risulta ~4330 m invece di 4478 m (la cima
aguzza viene “smussata” dal DEM). Con `--exag 1.2` il profilo risulta più slanciato.

## Stampa su Creality K2
- Entrambi stanno nel piatto di K2 / K2 Pro / K2 Plus.
- Ugello 0.4, layer 0.12–0.16 mm per i dettagli delle creste (layer adattivo consigliato).
- Infill 10–15 % (il modello è pieno: ~860 cm³ per la versione 6 km), 3 perimetri, nessun supporto.

## Rigenerare / personalizzare
```
pip install rasterio numpy
python make_cervino_stl.py out.stl --km 5 --size 200 --exag 1.0 --base 5 --grid 400
```
Le tile DEM vengono scaricate automaticamente in `dem_cache/`.
