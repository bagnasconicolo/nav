# Tavola periodica a cubi espositivi

Progetto parametrico (OpenSCAD) per stampare in 3D una tavola periodica fatta di
**cubi-vetrina staccabili** da 10 cm. Ogni cubo è una cornice sottile con una
fascia per **simbolo, numero e nome** e un **fondale curvo** scuro, come quelli
degli studi fotografici, su cui appoggiare l'oggetto. Si fissa al pannello con
**una sola vite**, nascosta dietro il fondale. Per cambiare elemento si cambia
solo il numero atomico.

![Tavola completa](anteprime/tavola_completa_3-4.png)

![Righe 2-3](anteprime/tavola_righe_2-3.png)

| Cubo singolo | Periodi 6-7 con segnaposto | Blocco f |
|---|---|---|
| ![Ferro](anteprime/cubo_ferro.png) | ![Periodi 6-7](anteprime/tavola_righe_6-7.png) | ![Blocco f](anteprime/blocco_f.png) |

## Design

- **Cornice**: 3 mm su lati e sopra, fascia da 16 mm sotto. Gli angoli
  dell'apertura sono raggiati a 3 mm e il bordo ha uno smusso a 45°. Il bordo
  esterno del fronte è arrotondato a 1,2 mm: tra due cubi accostati si forma una
  fuga d'ombra regolare, come tra le piastrelle.
- **Tipografia**: le stesse font di museo.chicubo.it, **Syne** e **IBM Plex**.
  Una sola riga, due colonne:
  - a sinistra il simbolo in **Syne Bold**, alto 8 mm;
  - a destra il numero atomico e il nome in **IBM Plex Mono SemiBold**, maiuscolo
    spaziato, alto 3 mm.

  Il numero è allineato alla cima del simbolo, il nome alla sua linea di base, con
  margini uguali in basso e a sinistra. I nomi lunghi si riducono da soli. Niente
  massa né altri dati.

  ![Fronte](anteprime/fronte_righe_6-7.png)
- **Fondale**: piano, curva da 24 mm di raggio e fondo in un unico pezzo, da
  stampare in un colore scuro opaco. Fa sparire spigoli e fondo e lascia vedere
  solo l'oggetto. Il piano è a filo della fascia, quindi la fascia non copre la
  base dell'oggetto.
- **Due colori al massimo sul cubo**: corpo neutro e scritta in rilievo. Il fondale
  è un pezzo a parte, quindi il suo colore non costa cambi filamento.

## File

| Percorso | Cosa contiene |
|---|---|
| `cubo_elemento.scad` | il modello: tutti i parametri sono in cima al file |
| `elementi.scad` | tabella dei 118 elementi (generata, non modificarla a mano) |
| `font/` | Syne e IBM Plex (licenza OFL), caricate direttamente dal modello |
| `dati/elementi.csv` | **dati di partenza**: nomi italiani, categoria (le masse ci sono ma non vengono stampate) |
| `strumenti/tavola.py` | genera la tabella, calcola i vicini, esporta tutti gli STL, fa lo schema del pannello |
| `stl/` | 118 elementi + 2 segnaposto già orientati per la stampa, più `comune_fondale.stl` e `comune_dima.stl` |
| `dati/pannello.svg`, `dati/fori_pannello.csv` | schema e quote di foratura del pannello |
| `strumenti/render_tavola.py`, `strumenti/anteprima.py` | le immagini di questa pagina (`USA_STL=1 … 1 10 1 18` per la tavola completa) |

## Uso

**Da OpenSCAD** (per un cubo alla volta): apri `cubo_elemento.scad`, nel Customizer
imposta `Z` e `parte = corpo`, poi F6 ed esporta l'STL. Per un testo libero metti
`Z = 0` e compila `simbolo_testo`, `nome_testo` e `numero_testo`.

**Tutti insieme** (consigliato, perché imposta da solo gli incastri in base ai vicini):

```bash
python3 strumenti/tavola.py genera            # solo se hai modificato dati/elementi.csv
python3 strumenti/tavola.py esporta           # tutti i cubi in stl/ (pochi minuti)
python3 strumenti/tavola.py esporta 26 Fe 79  # solo alcuni
python3 strumenti/tavola.py elenco            # posizioni e incastri di ogni cubo
python3 strumenti/tavola.py pannello          # rigenera pannello.svg e fori_pannello.csv
```

Serve OpenSCAD (testato con la 2021.01). Le font sono nella cartella `font/` e il
modello le carica da lì, quindi non vanno installate.
`trimesh` (`pip install trimesh`) è facoltativo: serve solo a salvare gli STL in binario.

## Com'è fatto

![Sezione](anteprime/sezione.png) ![Retro](anteprime/retro.png)

*Sezione laterale (il fronte è a destra) e retro.*

- **Fissaggio**: **una vite M4 a testa svasata** al centro della schiena. La testa
  resta a filo di un mozzo che fa anche da appoggio al fondale. Il fondale si
  infila dal fronte e la copre. In basso a sinistra, sotto il piano, c'è un foro
  cieco per una **spina Ø6** fissata nel pannello, che impedisce al cubo di ruotare.
- **Incastri tra cubi**: una linguetta a coda di rondine (45°) sul lato alto e sul
  lato destro entra nella scanalatura del cubo vicino. Corrono dal fronte al retro,
  quindi **ogni cubo si sfila in avanti da solo**. Lo script mette linguette e
  scanalature solo dove c'è un vicino, così il perimetro della tavola resta pulito.
  Dove le pareti ospitano una scanalatura sono rinforzate sotto il piano, quindi i
  rinforzi non si vedono.

## Stampa (Creality K2)

**Nessun supporto per nessun pezzo.**

- **Cubo**: già orientato sdraiato, retro sul piatto e scritta in alto. Lo svaso
  della vite si allarga verso l'alto e la rampa dietro la fascia è a 45°. L'unico
  ponte è di 12 mm. La cavità chiusa dietro la fascia è voluta: è vuota per
  risparmiare plastica.
- **Fondale**: in piedi sul suo profilo, alto 96 mm. È curvo, quindi sta in piedi
  da solo; un brim da 5 mm lo rende tranquillo.
- **Dima**: piatta.

Impostazioni consigliate: ugello 0,4, layer 0,2 mm, 3 perimetri, riempimento 15%,
PLA opaco (opacissimo il fondale, per non avere riflessi). Pareti e fondale da
1,6 mm sono esattamente 4 linee.

**Scritta di un altro colore (CFS)**: il testo è in rilievo di 0,6 mm sopra il
fronte, quindi basta **un solo cambio filamento sul layer a 100,0 mm**. Tutto quello
che sta sopra quella quota è solo testo. Con più cubi sullo stesso piatto il cambio
resta uno solo. In alternativa, `parte = testo` esporta solo le scritte, già
allineate, da assegnare a un altro filamento come parte separata.

**Quanti per piatto**: un cubo occupa 101,2 × 101,2 mm (linguette comprese).
Sulla **K2 Plus** (350 × 350) ne stanno **9**, su un piatto da 300 mm ne stanno 4.
I fondali, in piedi, ne stanno molti di più.

**Materiale**: circa 100 cm³ per cubo + 27 cm³ per il fondale, cioè **~155 g di
PLA per elemento** e **~19 kg per tutta la tavola** (120 pezzi). Per risparmiare:
- `parete = 1.2`: circa −15% sul cubo, ma è meno rigido.
- `lato` e `profondita` a 80 mm: circa −35%.
- Fondale in forex o cartoncino nero curvato al posto di quello stampato.

## Montaggio

**Pannello**: multistrato da 18 mm, **1809 × 1005 mm** (18 × 10 caselle, passo
100,5 mm, con una riga vuota prima del blocco f). In `dati/fori_pannello.csv` ci
sono le quote di ogni foro, misurate dal basso a sinistra guardando il pannello di
fronte. `dati/pannello.svg` è lo schema in scala 1:1.
`comune_dima.stl` è una dima leggera da appoggiare su ogni casella, con le
boccole guida per vite e spina.

Per **ogni cubo** servono:

- 1 vite **M4×16 a testa svasata piana** (ISO 10642, esagono incassato), su un
  **inserto filettato M4 per legno** nel pannello. Così il cubo si toglie e si
  rimette quante volte vuoi. La vite attraversa 4,5 mm di plastica.
- 1 spina Ø6 (legno o acciaio), incollata nel pannello e sporgente di 4 mm.

**Ordine**: fissa le spine, poi appoggia il cubo spingendolo dritto verso il
pannello lungo le linguette. Avvita la vite dal fronte, infila il fondale e
appoggia l'oggetto.

## Parametri principali (`cubo_elemento.scad`)

| Parametro | Default | Note |
|---|---|---|
| `lato`, `profondita` | 100 | dimensioni esterne |
| `parete`, `fondo`, `cielo`, `schiena` | 1,6 / 2 / 2 / 2 | spessori |
| `cornice`, `fascia_h` | 3 / 16 | cornice su lati e sopra, fascia con i testi |
| `raggio_apertura`, `raggio_bordo` | 3 / 1,2 | arrotondamenti |
| `h_simbolo`, `h_nome`, `h_numero` | 8 / 3 / 3 | altezza delle maiuscole in mm (sotto 3 il tratto diventa troppo sottile per un ugello da 0,4) |
| `font_simbolo`, `font_nome`, `font_numero` | Syne Bold / Plex Mono SemiBold | per il nome in tondo: `IBM Plex Sans:style=Medium` con `nome_maiuscolo = false` |
| `nome_maiuscolo`, `spaziatura_nome` | true / 1,12 | nome in maiuscolo spaziato |
| `numero_cifre` | 0 | 3 per numeri da catalogo (026) |
| `mostra_numero` | true | toglie il numero atomico |
| `testo_modo`, `testo_h` | rilievo / 0,6 | oppure `inciso` |
| `fondale_raggio`, `fondale_sp` | 24 / 1,6 | curva del fondale |
| `vite_d`, `svasatura_d` | 4,5 / 9,2 | per M3 cambia questi |
| `lingua_*`, `scanalatura_*` | true | li imposta lo script in base ai vicini |

Se cambi le dimensioni, rilancia `esporta` e `pannello`. Lo schema del pannello
legge le quote direttamente dal modello.
