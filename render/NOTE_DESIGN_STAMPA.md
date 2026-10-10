# MuLab: telaio per barre di scintillatore, note di design e stampa (v12)

Pensato per l'uso nelle scuole: robusto, smontabile e stampabile su una **Ender 3** senza
supporti. Il modello completo è generato da `scene_v12.py`, gli STL sono in `pezzi/` già
nell'orientamento di stampa.

## Regole di progetto seguite

1. **Niente filetti nella plastica.** Ogni vite va in un **inserto in ottone a caldo**:
   M3 nella scheda e nella scatola del Pi, M4 nei piedi.
2. **Niente perni sottili stampati.** La scheda appoggia su distanziali in ottone, non su
   pioli di plastica.
3. **Pareti di almeno 3 mm** nei pezzi strutturali, 2 mm nelle coperture. Raccordi da
   1,5–2,5 mm su tutti gli spigoli che si toccano.
4. **Faccia sul piatto con smusso a 45° da 0,6 mm**, non raccordata: un raccordo appoggiato al
   piatto stamperebbe a sbalzo, mentre lo smusso compensa anche l'elephant foot.
5. **Nessun supporto.**
   - I fori orizzontali sono **a goccia**, con punta a 45°.
   - Le finestre di alleggerimento hanno il **tetto a punta a 45°**.
   - I ponti sono corti, al massimo 16 mm (lo verifica `tools/check_print.py`).
6. **Tutto entra nel piatto 220 × 220 mm.** Il pezzo più grande è il piede: 55 × 150 × 30 mm.

## Pezzi stampati

| File | Q.tà | Ingombro (mm) | Come va sul piatto | Note |
|---|---|---|---|---|
| `piede.stl` | 2 | 55 × 150 × 30 | faccia inferiore | stesso pezzo a destra e a sinistra (ruotato di 180°); 4 inserti M4 sul fianco interno |
| `aggancio.stl` | 6 | 18 × 52 × 20 | in piedi, come montato | il tetto della tasca è un ponte da 10 mm; numero 1–3 inciso |
| `distanziale_24.stl` | 2 | 8,5 × 26 × 24 | in piedi | sotto l'aggancio 1 |
| `distanziale_50.stl` | 4 | 8,5 × 26 × 50 | in piedi | tra un aggancio e l'altro |
| `distanziale_44.stl` | 2 | 8,5 × 26 × 44 | in piedi | sopra l'aggancio 3, bloccato dal tappo |
| `tappo.stl` | 2 | 20 × 20 × 7 | capovolto (faccia superiore sul piatto) | vite M5 svasata nel foro assiale |
| `copertura.stl` | 3 | 28 × 33 × 5,4 | capovolta | copre il circuito della barra, lascia libero il KK |
| `culla_laterale.stl` | 2 | 39 × 128 × 28 | faccia inferiore | una delle due va **specchiata** nello slicer |
| `ponte_centrale.stl` | 1 | 70 × 128 × 28 | faccia inferiore | sostiene il centro della scheda |
| `scatola_calcolo.stl` | 1 | 128 × 50 × 23 | dorso sul piatto | Pi Zero 2 W, ventola 30 mm |
| `coperchio_calcolo.stl` | 1 | 104 × 50 × 3 | faccia esterna sul piatto | 3 viti M3 svasate |
| `cuffia_gpio.stl` | 1 | 24 × 10 × 15 | faccia superiore sul piatto | scarico della trazione del connettore GPIO |

Esito di `python tools/check_print.py pezzi/*.stl`:

| pezzo | piatto | sbalzi oltre 45° | luce massima dei ponti |
|---|---|---|---|
| aggancio | ok | 1 mm² | 9,6 mm |
| piede | ok | 7 mm² (bordi delle lettere del logo in rilievo, 0,8 mm) | 16,2 mm (lamature e sedi dei gommini) |
| scatola_calcolo | ok | 0 | 5,5 mm |
| tutti gli altri | ok | 0 | ≤ 1,2 mm |

## Impostazioni di stampa (Ender 3, ugello 0,4 mm)

- **Materiale:** PETG per tutto, in antracite più un colore d'accento per agganci e cuffia.
  Il PETG è più tenace e scorre meno sotto carico del PLA, e regge meglio un'aula d'estate.
- **Strato da 0,2 mm, 4 pareti, 5 strati sopra e sotto.** Riempimento gyroid al 40% per
  agganci, distanziali, tappi e culle; al 25% per piedi e scatola.
- **Ventola al 100% sui ponti** (agganci, piedi); per il resto, ventola al 30–50% per il PETG.
- **Niente brim**, solo uno skirt.
- **Prima prova:** stampa un aggancio e un distanziale, provali nel profilo vero e regola la
  linguetta (larghezza del collo 5,5 mm, testa 7,4 mm) prima di stampare la serie.

## Inserti e minuteria

| Cosa | Q.tà | Dove |
|---|---|---|
| inserti in ottone M4 (Ø esterno 5,6 mm) | 8 | piedi, 4 per piede (si usano i 2 anteriori) |
| inserti in ottone M3 (Ø esterno 4,0 mm) | 11 | culle (4), ponte (4), scatola del Pi (3, coperchio) |
| inserti in ottone M2,5 | 4 | piastrine del Pi nella scatola |
| distanziali in ottone M3 maschio-femmina 8 mm + viti M3×6 | 8 | scheda a 3 canali |
| viti M4 a testa zigrinata, lunghe circa 45 mm (o M4×45 + pomello) | 4 | culle → piedi |
| viti M5 svasate M5×10 (ISO 10642) | 2 | tappi |
| viti M5×16 ISO 4762 | 2 | montanti, dal basso |
| viti M5×8 ISO 7380 + dadi a T M5 | 2 | traversa |
| viti M5 a testa zigrinata + dadi a T M5 a inserimento frontale | 2 | scatola del Pi |
| viti M3×8 svasate | 3 | coperchio della scatola |
| distanziali M2,5 maschio-femmina 6 mm + viti M2,5×5 | 4 | Pi Zero 2 W |
| ventola 30 × 30 × 10 mm a 5 V | 1 | coperchio della scatola |
| gommini adesivi Ø 12 mm | 12 | 4 sotto i piedi, 8 sotto culle e ponte |

**Profili Bosch 20 × 20:** 2 × 250 mm (montanti) e 1 × 300 mm (traversa). Le estremità dei
montanti vanno **maschiate M5 in entrambi i lati**: sotto per la vite del piede, sopra per il
tappo.

## Come si monta

1. Inserti a caldo in tutti i pezzi stampati (saldatore a 220 °C con punta per inserti).
2. Montanti nei piedi, viti M5×16 dal basso; traversa nelle tasche dei piedi, viti M5×8 nei
   dadi a T.
3. In ciascun montante, dal basso verso l'alto (infilando i pezzi dalla cima): distanziale 24, aggancio 1, distanziale 50, aggancio 2,
   distanziale 50, aggancio 3, distanziale 44. Le barre vanno nelle tasche degli agganci
   mentre si impila.
4. Tappo con vite M5 svasata: chiudendolo si blocca tutta la colonna.
5. Modulo scheda: culle e ponte sotto la scheda (distanziali in ottone), poi si avvicina il
   modulo ai piedi e si stringono i 4 pomelli M4. Per toglierlo basta svitare i 4 pomelli e
   scollegare i KK.
6. Modulo di calcolo: due pomelli M5 nei dadi a T a inserimento frontale, nella scanalatura
   esterna del montante destro.

## Punti ancora da verificare con i pezzi veri

- Quote della scanalatura del profilo che usi (apertura 6 mm, labbri 1,8 mm, nel modello).
- Gioco della tasca dell'aggancio sulla barra rivestita (0,5 mm per lato nel modello).
- Lunghezza effettiva dei pomelli M4 una volta stampate le culle.
