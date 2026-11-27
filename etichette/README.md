# Generatore di etichette per minerali

Etichette stampabili (A4) per la collezione, con **nome**, **formula chimica**, **località**,
**Mindat ID**, **QR code** (link alla pagina Mindat) e **bandierina** del paese.
I dati vengono cercati sull'API di [Mindat](https://api.mindat.org).

## Avvio

1. Salva la chiave API in un file `.mindat_key` in questa cartella (è nel `.gitignore`,
   non viene mai committata), oppure usa la variabile `MINDAT_API_KEY`.
2. Avvia il server locale (serve la pagina e inoltra le richieste a Mindat):

   ```bash
   python3 server.py
   ```

3. Apri <http://localhost:8765>.

In alternativa si può aprire `index.html` direttamente e incollare la chiave nelle
impostazioni (resta solo nel browser), ma Mindat potrebbe bloccare le richieste dal browser (CORS):
in quel caso usa `server.py`.

## Import in blocco (etichette già complete)

Nel riquadro **Importa in blocco da Mindat**:

- **ID utente**: `server.py` legge lo schema dell'API Mindat, cerca un endpoint per le
  collezioni/esemplari e scarica tutti i tuoi esemplari. Se l'API non lo espone, mostra
  l'elenco degli endpoint disponibili.
- **Elenco incollato**, una riga per esemplare: `ID minerale (o nome) ; località (ID Mindat o testo) ; N. catalogo`.
- **CSV** (anche solo con `mindat_id`).

In tutti i casi nome, formula, località, paese e bandiera vengono completati da Mindat.
Il pulsante **Completa da Mindat i selezionati** riempie i campi mancanti di esemplari già presenti.

## Uso

- **Minerale → Cerca**: cerca per nome (o numero = Mindat ID) e compila nome, ID, formula.
- **Località → Cerca**: cerca la località su Mindat; il paese e la bandiera si compilano da soli
  (modificabili: codice ISO tipo `it`, `fr`, `us`, `gb-eng`…).
- Formula: `_2_` = pedice, `^2+^` = apice (es. `Fe^2+^_3_Al_2_(SiO_4_)_3_`).
- La collezione è salvata nel browser; usa **Esporta/Importa CSV** per backup o per caricare
  una lista (colonne: `numero, minerale, mindat_id, formula, localita, mindat_loc_id, paese, codice_paese, note, qr`).
- Seleziona gli esemplari e premi **Stampa**: dimensioni, carattere, intestazione, copie e
  margini si regolano nelle impostazioni. Stampa al 100% (senza "adatta alla pagina").

Bandiere: [flag-icons](https://github.com/lipis/flag-icons) (MIT). QR: [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) (MIT).
