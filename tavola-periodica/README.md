# Tavola periodica a cubi espositivi

Progetto parametrico (OpenSCAD) per stampare in 3D una tavola periodica fatta di
**cubi-vetrina staccabili** da 10 cm. Ogni cubo è aperto davanti quasi per intero e
ha solo una sottile fascia con **numero, simbolo e nome**. C'è un canale nascosto
per una striscia LED e un vano tecnico sotto il piano espositivo, e il cubo si fissa
al pannello con **una sola vite**. Per cambiare elemento si cambia solo il numero
atomico.

![Righe 2-3](anteprime/tavola_righe_2-3.png)

| Cubo singolo | Periodi 6-7 con segnaposto | Blocco f |
|---|---|---|
| ![Ferro](anteprime/cubo_ferro.png) | ![Periodi 6-7](anteprime/tavola_righe_6-7.png) | ![Blocco f](anteprime/blocco_f.png) |

## File

| Percorso | Cosa contiene |
|---|---|
| `cubo_elemento.scad` | il modello: tutti i parametri sono in cima al file |
| `elementi.scad` | tabella dei 118 elementi (generata, non modificarla a mano) |
| `dati/elementi.csv` | **dati di partenza**: nomi italiani, categoria, masse (al momento non stampate) |
| `strumenti/tavola.py` | genera la tabella, calcola i vicini, esporta tutti gli STL, fa lo schema del pannello |
| `stl/` | 118 elementi + 2 segnaposto già orientati per la stampa, più `comune_pavimento.stl` e `comune_dima.stl` |
| `dati/pannello.svg`, `dati/fori_pannello.csv` | schema e quote di foratura del pannello |
| `strumenti/render_tavola.py`, `strumenti/anteprima.py` | le immagini qui sopra |

## Uso

**Da OpenSCAD** (per un cubo alla volta): apri `cubo_elemento.scad`, nel Customizer
imposta `Z` e `parte = corpo`, poi F6 ed esporta l'STL. Per un testo libero metti
`Z = 0` e compila `simbolo_testo` e `nome_testo` (`mostra_numero` per il numero).

**Tutti insieme** (consigliato, perché imposta da solo gli incastri in base ai vicini):

```bash
python3 strumenti/tavola.py genera            # solo se hai modificato dati/elementi.csv
python3 strumenti/tavola.py esporta           # tutti i cubi in stl/ (pochi minuti)
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

- **Fronte quasi tutto aperto**: ai lati l'apertura arriva fino alle pareti. Restano
  solo una visiera da 10 mm in alto e una fascia da 13 mm in basso. La fascia ha una
  riga sola: <sup>26</sup>**Fe** a sinistra, *Ferro* a destra. I nomi lunghi si
  rimpiccioliscono da soli. L'apertura utile è 96,8 × 77 mm.
- **Luce**: dietro la visiera c'è un piano a 45° con un canale per una **striscia
  LED COB da 5 mm**. La luce va verso l'oggetto e chi guarda non vede la striscia.
  I fili passano in un tunnel Ø3,5 nello spigolo alto destro ed escono dal retro.
- **Piano espositivo e vano tecnico**: il pavimento (`comune_pavimento.stl`) è un
  pezzo separato, a filo della fascia. Sotto c'è un vano basso per i cavi con un
  passacavo Ø7 sul retro. La tacca sul bordo del pavimento serve a sollevarlo.
- **Fissaggio**: **una vite M4 a testa svasata** nell'angolo basso a sinistra, sotto
  il pavimento, quindi invisibile. Si stringe con una chiave a brugola a testa
  sferica passando sopra la fascia (bastano 4–5° di inclinazione). Nell'angolo
  opposto c'è un foro cieco per una **spina Ø6** fissata nel pannello, che impedisce
  al cubo di ruotare attorno alla vite.
- **Incastri tra cubi**: una linguetta a coda di rondine (45°) sul lato alto e sul
  lato destro entra nella scanalatura del cubo vicino. Corrono dal fronte al retro,
  quindi **ogni cubo si sfila in avanti da solo**. Lo script mette linguette e
  scanalature solo dove c'è un vicino, così il perimetro della tavola resta pulito.

## Stampa (Creality K2 / qualunque FDM)

Gli STL sono **già orientati sdraiati**: retro sul piatto e fronte con la scritta in
alto. **Zero supporti**: lo svaso della vite si allarga verso l'alto, il canale LED
e la rampa dietro la fascia sono a 45° e l'unico ponte è di 9 mm. La cavità chiusa
dietro la fascia è voluta: è vuota per risparmiare plastica.

Impostazioni consigliate: ugello 0,4, layer 0,2 mm, 3 perimetri, riempimento 15%,
PLA opaco. Le pareti da 1,6 mm sono esattamente 4 linee.

**Scritta di un altro colore (CFS)**: il testo è in rilievo di 0,6 mm sopra il
fronte, quindi basta **un solo cambio filamento sul layer a 100,0 mm**. Tutto quello
che sta sopra quella quota è solo testo. Se metti più cubi sullo stesso piatto, il
cambio è uno solo per tutto il piatto, quindi lo spreco di spurgo è minimo. In
alternativa, `parte = testo` esporta solo le scritte, già allineate, da caricare
come parte separata e assegnare a un altro filamento.

Facoltativo: un secondo cambio a **97,0 mm** colora anche la fascia e la visiera con
il colore della categoria (palette in `COLORI_CORNICE` in `strumenti/tavola.py`,
render con `CORNICE=1`).

**Quanti per piatto**: un cubo occupa 101,2 × 101,2 mm (linguette comprese). Sul
piatto 350 × 350 della **K2 Plus** ne stanno **9** (3 × 3). Su un piatto da 300 mm
ne stanno 4.

**Materiale**: circa 110 cm³ per cubo (~135 g di PLA) più 18 cm³ (~22 g) di
pavimento. Per tutta la tavola (120 cubi) servono **circa 18–19 kg**. Per
risparmiare ancora:
- `parete = 1.2`: circa −15%, ma i cubi sono meno rigidi.
- `lato` e `profondita` a 80 mm: circa −35%.
- Pavimento stampato con riempimento basso, oppure ritagliato da cartoncino o
  forex da 2 mm.

## Montaggio

**Pannello**: multistrato da 18 mm, **1809 × 1005 mm** (18 × 10 caselle, passo
100,5 mm, con una riga vuota prima del blocco f). In `dati/fori_pannello.csv` ci
sono le quote di ogni foro, misurate dal basso a sinistra guardando il pannello di
fronte. `dati/pannello.svg` è lo schema in scala 1:1.
`comune_dima.stl` è una dima leggera da appoggiare su ogni casella: ha le boccole
guida per vite e spina e due segni per i fori dei cavi.

Per **ogni cubo** servono:

- 1 vite **M4×16 a testa svasata piana** (ISO 10642, esagono incassato), su un
  **inserto filettato M4 per legno** nel pannello. Così il cubo si toglie e si
  rimette quante volte vuoi. La vite attraversa 6,6 mm di plastica: scegli la
  lunghezza in base all'inserto.
- 1 spina Ø6 (legno o acciaio), incollata nel pannello e sporgente di 4 mm.
- ~90 mm di striscia LED COB da 5 mm + 2 fili. I fori passacavo del pannello
  permettono un cablaggio a bus dietro il pannello.

**Ordine**: fissa le spine, poi i cubi. Ogni cubo entra spingendolo dritto verso il
pannello lungo le linguette. Fissa la vite dal vano tecnico, poi appoggia il
pavimento.

## Parametri principali (`cubo_elemento.scad`)

| Parametro | Default | Note |
|---|---|---|
| `lato`, `profondita` | 100 | dimensioni esterne |
| `parete`, `fondo`, `cielo`, `schiena` | 1,6 / 2 / 2 / 1,6 | spessori |
| `fascia_h`, `visiera_h` | 13 / 10 | altezza della fascia con i testi e della visiera |
| `dim_simbolo`, `dim_numero`, `dim_nome` | 7,5 / 3,4 / 4,6 | dimensioni dei testi |
| `mostra_numero` | true | toglie il numero atomico |
| `testo_modo`, `testo_h` | rilievo / 0,6 | oppure `inciso` |
| `led_larghezza` | 5,5 | 8,5 per strisce da 8 mm (in quel caso alza `visiera_h`) |
| `vite_d`, `svasatura_d` | 4,5 / 9,2 | per M3 cambia questi |
| `lingua_*`, `scanalatura_*` | true | li imposta lo script in base ai vicini |

Se cambi le dimensioni, rilancia `esporta` e `pannello`. Lo schema del pannello
legge le quote direttamente dal modello.
