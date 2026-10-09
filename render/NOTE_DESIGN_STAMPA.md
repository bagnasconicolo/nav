# Telaio per barre di scintillatore: note su design e stampa

## Struttura (v4)

La base non è più un pezzo stampato grande: la traversa longitudinale è un **profilo Bosch
20 × 20 × 300 mm**, uguale ai montanti (20 × 20 × 250 mm). Stampati restano solo due piedi
compatti, che tengono sia il montante sia l'estremità della traversa.

## Pezzi stampati

| Pezzo | Q.tà | Ingombro (mm) | Orientamento di stampa | File |
|---|---|---|---|---|
| Piede | 2, identici (uno ruotato di 180°) | 54 × 150 × 30 | piatto, faccia inferiore sul piatto | `pezzi/piede.stl` |
| Aggancio | 6, identici | 51 × 18 × 20 (con linguetta) | come montato: linguetta verticale | `pezzi/aggancio.stl` |
| Distanziale da 10 mm | 24 (12 per lato) | 26 × 8,5 × 9,9 (passo 10) | come montato: linguetta verticale | `pezzi/distanziale.stl` |
| Tappo | 2 | 20 × 20 × 10 | capovolto, faccia superiore sul piatto | `pezzi/tappo.stl` |

Ogni piede ha:
- una sede verticale 20 × 20 per il montante, fissato dal basso con una vite M5 nel foro assiale;
- una tasca laterale in cui entrano 16 mm della traversa, fissata dal basso con una vite M5 a
  testa bombata in un dado a T (Nutenstein M5) infilato nella scanalatura inferiore della traversa;
- due nervature di rinforzo e due sedi da 12,6 mm di diametro per i gommini antiscivolo.

Nell'STL il distanziale è alto 9,9 mm: il decimo di gioco serve a non far crescere la pila
se la stampa esce leggermente più alta. Se misuri i pezzi esatti, scalalo in Z a 10 mm.

## Materiale da acquistare

- Profilo Bosch 20 × 20: 2 × 250 mm (montanti) + 1 × 300 mm (traversa), tagli a 90° sbavati
- 2 × M5×16 ISO 4762 (montanti, dal basso nel foro assiale filettato)
- 2 × M5×8 ISO 7380 a testa bombata + 2 dadi a T M5 per scanalatura da 20 (traversa)
- 4 gommini adesivi Ø 12 × 2–3 mm
- 2 tappi per profilo 20 × 20, se non li stampi

## Consigli sul design

1. **Verifica le misure del profilo prima di stampare.** Nel modello la scanalatura ha
   un'apertura di 6 mm, labbri da 1,8 mm e un foro assiale di 4,2 mm. Misura con il calibro il
   profilo che hai, oppure prendi le misure dal datasheet del fornitore. La linguetta a T va
   adattata a quelle quote.
2. **Il foro assiale va filettato M5.** La vite dal basso non tiene se l'estremità del profilo
   non è maschiata. Se il foro è già M5, ok; altrimenti serve un maschio M5.
3. **Bloccaggio in quota.** La pila di distanziali sostiene gli agganci, ma niente impedisce alla
   colonna di sollevarsi. Due soluzioni:
   - riempire la scanalatura fino in cima e far premere il tappo sull'ultimo distanziale
     (servono distanziali anche da 5 mm per chiudere il gioco);
   - mettere un grano M4 nella piastra posteriore dell'aggancio, che spinge sul fondo della
     scanalatura.
4. **Meno pezzi.** 24 distanziali da 10 mm sono tanti e la tolleranza si somma: 5 pezzi a
   ±0,1 mm fanno ±0,5 mm. Puoi usare distanziali di altezze diverse (5, 10, 20 e 50 mm) oppure
   un unico distanziale da 50 mm tra un aggancio e l'altro.
5. **Inserimento solo dall'alto.** Per cambiare la barra in basso devi sfilare tutto quello che
   sta sopra. Una linguetta a rotazione (testa più stretta in un verso, si inserisce di fronte
   e si gira di 90°, come i dadi a T drop-in) permette di montare ogni pezzo a qualunque
   altezza.
6. **Barre nelle tasche.** La pellicola ha uno spessore variabile. Conviene un invito
   smussato da 0,5–1 mm all'imbocco della tasca e una piccola nervatura schiacciabile o un
   pezzetto di gommapiuma sul fondo, così la barra non balla. Stampa prima un campione di
   tasca con gioco 0,2 / 0,3 / 0,4 mm per lato.
7. **Squadratura della base.** Se la tasca del piede è stretta sulla traversa (gioco 0,15 mm),
   è la traversa a mettere in squadra i due montanti. Per una rigidità maggiore puoi aggiungere
   due squadrette Bosch 20 tra traversa e montanti, nascoste sul lato posteriore. Se vuoi
   fissare il telaio al banco, aggiungi un foro passante in ciascun piede.
8. **Cavi.** Una clip stampata da agganciare nella scanalatura anteriore del montante sinistro
   tiene i fili fermi. Fissa il cavo vicino al circuito con una fascetta, così il morsetto
   non lavora a strappo.
9. **Tappi.** I tappi originali per profili 20 × 20 costano poco e hanno alette elastiche
   migliori. Se li stampi, le alette sono sottili e lavorano tra gli strati: stampali in PETG.

## Consigli di stampa (Ender 3, ugello 0,4 mm)

- **Materiale:** PETG per agganci e distanziali (più tenace e con meno scorrimento sotto
  carico del PLA). PLA o PETG per i piedi (meglio PETG, se il telaio resta sotto carico a lungo).
- **Strati e pareti:** strato da 0,2 mm. Agganci e distanziali con 4 pareti e 40% di
  riempimento (la linguetta a T così è quasi piena). Piedi con 4 pareti e 30% gyroid.
- **Primo strato:** compensa l'elephant foot (0,1–0,2 mm), altrimenti la linguetta non entra
  nella scanalatura e i distanziali impilati si sommano in altezza.
- **Tolleranze:** sulla Ender 3 i fori escono di solito più stretti. Nel modello la sede del
  montante ha 0,15 mm di gioco per lato: se è troppo stretta, porta il gioco a 0,25 mm o usa
  l'espansione orizzontale per i fori nello slicer.
- **Lamatura delle viti M5:** si apre sulla faccia a contatto con il piatto. Il gradino tra la
  lamatura e il foro passante (sia per le M5×16 sia per le M5×8) è un piccolo ponte: stampalo così oppure aggiungi uno strato
  sacrificale da forare dopo.
- **Piede:** la tasca della traversa si apre di lato e il suo tetto è un ponte di 20 mm, che
  si stampa senza supporti. Le nervature a 45° sono autoportanti.
- **Aggancio:** stampato come montato, il tetto della tasca è un ponte da circa 46 mm. Con la
  ventola al 100% esce pulito. La linguetta a T sta nel piano degli strati, quindi lavora nel
  verso forte.
- **Prima di stampare tutto:** stampa un solo aggancio e un distanziale, provali nel profilo
  vero e poi correggi le quote.
