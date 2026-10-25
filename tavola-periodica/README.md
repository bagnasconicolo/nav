# Tavola periodica a cubi espositivi

Progetto parametrico (OpenSCAD) per stampare in 3D una tavola periodica fatta di
**cubi-vetrina staccabili** da 10 cm: ogni cubo è aperto davanti, ha una targhetta
con numero, simbolo, nome e massa atomica, un canale nascosto per una striscia LED,
un vano tecnico sotto il piano espositivo e si fissa al pannello con **una sola vite**.
Per fare un elemento diverso si cambia solo il numero atomico.

![Righe 2-3](anteprime/tavola_righe_2-3.png)

| Cubo singolo | Periodi 6-7 con segnaposto | Blocco f |
|---|---|---|
| ![Ferro](anteprime/cubo_ferro.png) | ![Periodi 6-7](anteprime/tavola_righe_6-7.png) | ![Blocco f](anteprime/blocco_f.png) |

## File

| Percorso | Cosa contiene |
|---|---|
| `cubo_elemento.scad` | il modello: tutti i parametri sono in cima al file |
| `elementi.scad` | tabella dei 118 elementi (generata, non modificarla a mano) |
| `dati/elementi.csv` | **dati di partenza**: nomi italiani, masse (valori IUPAC convenzionali, `[ ]` = isotopo più stabile), categoria |
| `strumenti/tavola.py` | genera la tabella, calcola i vicini, esporta tutti gli STL, fa lo schema del pannello |
| `stl/` | 118 elementi + 2 segnaposto già pronti per la stampa, più `comune_pavimento.stl` e `comune_dima.stl` |
| `dati/pannello.svg`, `dati/fori_pannello.csv` | schema e quote di foratura del pannello |
| `strumenti/render_tavola.py`, `strumenti/anteprima.py` | le immagini qui sopra |

## Uso

**Da OpenSCAD** (per un cubo alla volta): apri `cubo_elemento.scad`, nel Customizer
imposta `Z` e `parte = corpo`, poi F6 ed esporta l'STL. Per un testo libero metti
`Z = 0` e compila `numero_testo`, `simbolo_testo`, `nome_testo` e `massa_testo`.

**Tutti insieme** (consigliato, perché imposta da solo gli incastri in base ai vicini):

```bash
python3 strumenti/tavola.py genera            # solo se hai modificato dati/elementi.csv
python3 strumenti/tavola.py esporta           # tutti i cubi in stl/ (circa 5 min con 4 core)
python3 strumenti/tavola.py esporta 26 Fe 79  # solo alcuni
python3 strumenti/tavola.py elenco            # posizioni e incastri di ogni cubo
python3 strumenti/tavola.py pannello          # rigenera pannello.svg e fori_pannello.csv
```

Serve OpenSCAD (testato con la 2021.01) e il font **Inter** (gratuito, Google Fonts).
Senza Inter OpenSCAD usa un font di ripiego: in quel caso cambia `font_simbolo` e `font_testo`.
`trimesh` (`pip install trimesh`) è facoltativo: serve solo a salvare gli STL in binario.

## Com'è fatto il cubo

![Sezione](anteprime/sezione.png) ![Retro](anteprime/retro.png)

*Sezione laterale (il fronte è a destra) e retro.*

- **Cornice frontale**: bordi da 4 mm ai lati, visiera da 15 mm in alto e fascia da
  24 mm in basso con i testi in rilievo. Il bordo dell'apertura ha uno smusso a 45°.
  I testi si rimpiccioliscono da soli quando sono lunghi (es. *Rutherfordio*).
- **Luce**: dietro la visiera c'è un piano a 45° con un canale da 10,5 × 2 mm per una
  striscia LED da 10 mm (COB consigliata, niente puntini). La luce va verso l'oggetto
  e chi guarda non vede la striscia. I fili passano in un tunnel Ø4 dentro lo
  smusso dello spigolo alto destro ed escono dal retro.
- **Piano espositivo e vano tecnico**: il pavimento (`comune_pavimento.stl`) è un
  pezzo separato che si appoggia a filo della fascia. Sotto c'è un vano alto ~19 mm
  per alimentatore e cavi, con un passacavo Ø8 sul retro. La tacca sul bordo
  posteriore del pavimento serve a sollevarlo e lascia passare un cavo.
- **Fissaggio**: **una vite M4 a brugola** nell'angolo basso a sinistra, dentro il
  vano tecnico, quindi nascosta dal pavimento. Si stringe con una chiave a L o con
  un inserto a testa sferica. Nell'angolo opposto c'è un foro cieco per una **spina
  Ø6** fissata nel pannello, che impedisce al cubo di ruotare attorno alla vite.
- **Incastri tra cubi**: una linguetta a coda di rondine (45°) sul lato alto e sul
  lato destro entra nella scanalatura del cubo vicino. Corrono dal fronte al retro,
  quindi **ogni cubo si sfila in avanti da solo** anche se è circondato da altri.
  Lo script mette linguette e scanalature solo dove c'è davvero un vicino, così il
  perimetro della tavola resta pulito.
- **Magneti** (facoltativi): sedi per 2 magneti al neodimio 6×3 mm su ogni fianco
  che ha un vicino. Tengono i cubi accostati a filo.

## Stampa

Gli STL sono **già orientati**: retro sul piatto e fronte in alto. **Non servono
supporti**: le sporgenze sono tutte a 45° o ponti di al massimo 19 mm, e la cavità
chiusa dietro la fascia è voluta.

Impostazioni consigliate: layer 0,2 mm, 3 perimetri, riempimento 15%, PLA opaco.

**Tre colori con un solo ugello**, usando i cambi filamento in altezza (M600 o
"aggiungi pausa/cambio colore" nello slicer):

| Altezza (mm) | Cosa si stampa da lì in poi | Filamento |
|---|---|---|
| 0 | corpo | neutro (bianco o grigio chiaro) |
| **96,0** | cornice frontale | colore della categoria |
| **100,0** | testi in rilievo | nero o bianco |

I colori delle categorie usati nelle immagini sono in `COLORI_CORNICE`
in `strumenti/tavola.py`. Con un AMS o un MMU fai la stessa cosa assegnando i
colori per altezza.

**Materiale**: circa 160 cm³ per cubo, cioè **~150–180 g di PLA** a seconda dello
slicer. Per tutta la tavola (120 cubi) servono **circa 18–21 kg** e diverse
centinaia di ore di stampa. Con `parete = 1.6` risparmi circa il 15%. Con `lato`
e `profondita` a 80 mm circa il 35%.

## Montaggio

**Pannello**: multistrato da 18 mm, **1809 × 1005 mm** (18 × 10 caselle, passo
100,5 mm, con una riga vuota prima del blocco f). In `dati/fori_pannello.csv` ci
sono le quote di ogni foro, misurate dal basso a sinistra guardando il pannello di
fronte. `dati/pannello.svg` è lo schema in scala 1:1.
`comune_dima.stl` è una dima da appoggiare su ogni casella: ha le boccole guida per
vite e spina e due segni per i fori dei cavi.

Per **ogni cubo** servono:

- 1 vite M4×16 a brugola (ISO 4762), su un **inserto filettato M4 per legno**
  nel pannello. Così il cubo si toglie e si rimette quante volte vuoi. Sotto la
  testa ci sono 7,2 mm di plastica.
- 1 spina Ø6 (legno o acciaio), incollata nel pannello e sporgente di 5–6 mm.
- 0–4 magneti 6×3 mm (432 in tutto). **Polarità**: tutti i magneti del lato destro
  con il Nord verso l'esterno, tutti quelli del lato sinistro con il Sud verso
  l'esterno. Usa sempre lo stesso magnete di riferimento per controllare.
- ~88 mm di striscia LED + 2 fili. I fori passacavo del pannello permettono un
  cablaggio a bus dietro il pannello.

**Ordine**: fissa le spine, poi i cubi. Ogni cubo entra spingendolo dritto verso il
pannello lungo le linguette. Fissa la vite dal vano tecnico, poi appoggia il
pavimento.

## Parametri principali (`cubo_elemento.scad`)

| Parametro | Default | Note |
|---|---|---|
| `lato`, `profondita` | 100 | dimensioni esterne |
| `parete`, `fondo`, `cielo`, `schiena` | 2 / 2,4 / 2,4 / 2,4 | spessori |
| `fascia_h`, `visiera_h` | 24 / 15 | altezza della targhetta e della visiera |
| `testo_modo`, `testo_h` | rilievo / 0,6 | oppure `inciso` |
| `led_larghezza` | 10,5 | 8,5 per strisce da 8 mm |
| `vite_d`, `testa_d`, `testa_h` | 4,5 / 7,6 / 4,2 | per M3 o M5 cambia questi |
| `lingua_*`, `scanalatura_*` | true | li imposta lo script in base ai vicini |
| `magneti`, `magnete_d`, `magnete_h` | true / 6,3 / 3,2 | sedi magneti |

Se cambi le dimensioni, rilancia `esporta` e `pannello`. Lo schema del pannello
legge le quote direttamente dal modello.
