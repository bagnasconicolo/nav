# NAV · Mappa da campo

Web-app responsive (desktop + smartphone) per consultare sul campo ortofoto, mappe
di base e immagini georeferenziate, con posizione GPS in tempo reale.

## Cosa include

**Livelli disponibili** (tutti con visibilità, trasparenza e ordine modificabili):

| Livello | Tipo | Fonte |
|---|---|---|
| OpenStreetMap | mappa stradale | tile OSM |
| OpenTopoMap | topografica / curve di livello | tile OpenTopoMap |
| Ortofoto AGEA 2024 | ortofoto | WMS CSI Piemonte |
| Ortofoto AGEA 2021 | ortofoto | WMS CSI Piemonte |
| Ortofoto 1980-90 | ortofoto storica | WMS CSI Piemonte |
| Foto/documenti georef. | immagini | i tuoi GeoTIFF (cartella `overlays/`) |

**Funzioni**
- Posizione GPS in tempo reale con cerchio di incertezza (accuratezza in metri).
- Coordinate live del centro mirino: tocca la casella in alto a sinistra per
  ciclare tra **gradi decimali (DD)**, **gradi-primi-secondi (DMS)** e **UTM 32N**.
- Pannello Livelli: mostra/nascondi (👁), trasparenza (slider), ordine (trascina ⋮⋮
  o usa ▲▼). In alto nella lista = sopra sulla mappa.
- L'impostazione dei livelli viene ricordata (localStorage). Tasto **Reset** per ripristinare.
- Pulsante **Inquadra le mie foto** per centrare le immagini georeferenziate.

## Come avviarla

L'app è un sito statico. Il GPS del browser però richiede **HTTPS** oppure **localhost**.

### Prova in locale (sul computer)
```bash
cd site
python3 -m http.server 8848
```
Apri <http://localhost:8848> — qui il GPS funziona perché è localhost.

### Uso sul campo (da smartphone) → serve HTTPS
Pubblica la cartella `site/` su un hosting con HTTPS. La via più semplice e gratuita
è **GitHub Pages**:
1. Crea un repository e carica il contenuto di `site/`.
2. Settings → Pages → Deploy from branch → `main` / root.
3. Apri l'URL `https://…github.io/…` dal telefono: il GPS funzionerà.

(In alternativa: Netlify, Cloudflare Pages, o qualsiasi hosting statico con HTTPS.)

## Aggiungere altre immagini georeferenziate

I GeoTIFF devono essere in **EPSG:4326 (WGS84), north-up**. Poi:
```bash
python3 tools/build_overlays.py /cartella/con/i/tif
```
Lo script converte i .tif in immagini web dentro `overlays/` e riscrive `overlays.js`
con i bounding box. Ricarica la pagina: le nuove immagini compaiono nel pannello.
Richiede `Pillow` (`pip install pillow`).

## Struttura
```
site/
├─ index.html         pagina
├─ style.css          stile (UI da campo, tema scuro ad alto contrasto)
├─ app.js             logica: livelli, GPS, coordinate
├─ overlays.js        elenco immagini georef. + bounding box (generato)
├─ overlays/          immagini web + manifest.json
├─ vendor/            Leaflet 1.9.4 + proj4 (locali, per uso offline del guscio)
└─ tools/build_overlays.py   rigenera gli overlay dai GeoTIFF
```

## Note tecniche
- I livelli WMS sono richiesti in EPSG:3857 con `crossOrigin` (CORS) per evitare il
  blocco ORB di Chrome sulle immagini cross-origin.
- Gli overlay sono `L.imageOverlay` posizionati sul bounding box calcolato dai tag
  GeoTIFF (ModelTiepoint + ModelPixelScale).
- Le librerie sono servite in locale: il guscio dell'app si carica anche con rete
  scarsa; solo i tile delle mappe richiedono connettività.
