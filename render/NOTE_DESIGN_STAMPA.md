# Telaio per barre di scintillatore: note su design e stampa

## Pezzi stampati (v3)

| Pezzo | Q.tà | Ingombro (mm) | Orientamento di stampa | File |
|---|---|---|---|---|
| Semibase (piede + mezza traversa) | 2, identiche | 204 × 150 × 30 | piatta, faccia inferiore sul piatto | `pezzi/semibase.stl` |
| Aggancio | 6, identici | 51 × 18 × 20 (con linguetta) | come montato: linguetta verticale | `pezzi/aggancio.stl` |
| Distanziale da 10 mm | 24 (12 per lato) | 26 × 8,5 × 9,9 (passo 10) | come montato: linguetta verticale | `pezzi/distanziale.stl` |
| Tappo | 2 | 20 × 20 × 10 | capovolto, faccia superiore sul piatto | `pezzi/tappo.stl` |

Il piatto della Ender 3 misura 220 × 220 mm. Una semibase occupa 204 × 150 mm, quindi entra
con circa 8 mm di margine per lato: usa skirt a 3 mm oppure nessun skirt, e niente brim largo.

Le due semibasi sono **lo stesso pezzo** ruotato di 180°. Si uniscono al centro con un giunto a
mezzo legno affiancato (sovrapposizione di 36 mm) e 2 viti M4×20 a testa cilindrica con dado
esagonale nell'alloggiamento.

Nell'STL il distanziale è alto 9,9 mm: il decimo di gioco serve a non far crescere la pila
se la stampa esce leggermente più alta. Se misuri i pezzi esatti, scalalo in Z a 10 mm.

## Minuteria

- 2 × M5×16 ISO 4762 (fissano i montanti dal sotto della base)
- 2 × M4×20 ISO 4762 + 2 dadi M4 (giunto della traversa)

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
7. **Giunto della base.** Due spine di centraggio (o un incastro a coda di rondine) nel giunto
   a mezzo legno aiutano l'allineamento. Sotto i piedi conviene mettere 4 gommini adesivi;
   un foro passante nei piedi permette di fissare il telaio al banco.
8. **Cavi.** Una clip stampata da agganciare nella scanalatura anteriore del montante sinistro
   tiene i fili fermi. Fissa il cavo vicino al circuito con una fascetta, così il morsetto
   non lavora a strappo.
9. **Tappi.** I tappi originali per profili 20 × 20 costano poco e hanno alette elastiche
   migliori. Se li stampi, le alette sono sottili e lavorano tra gli strati: stampali in PETG.

## Consigli di stampa (Ender 3, ugello 0,4 mm)

- **Materiale:** PETG per agganci e distanziali (più tenace e con meno scorrimento sotto
  carico del PLA). PLA o PETG per la base.
- **Strati e pareti:** strato da 0,2 mm. Agganci e distanziali con 4 pareti e 40% di
  riempimento (la linguetta a T così è quasi piena). Base con 3 pareti e 25% gyroid.
- **Primo strato:** compensa l'elephant foot (0,1–0,2 mm), altrimenti la linguetta non entra
  nella scanalatura e i distanziali impilati si sommano in altezza.
- **Tolleranze:** sulla Ender 3 i fori escono di solito più stretti. Nel modello la sede del
  montante ha 0,15 mm di gioco per lato: se è troppo stretta, porta il gioco a 0,25 mm o usa
  l'espansione orizzontale per i fori nello slicer.
- **Lamatura delle viti M5:** si apre sulla faccia a contatto con il piatto. Il gradino tra la
  lamatura e il foro passante è un piccolo ponte: stampalo così oppure aggiungi uno strato
  sacrificale da forare dopo.
- **Alloggiamento del dado M4:** è sulla faccia verticale, con un vertice dell'esagono verso
  l'alto, quindi si stampa senza supporti.
- **Aggancio:** stampato come montato, il tetto della tasca è un ponte da circa 46 mm. Con la
  ventola al 100% esce pulito. La linguetta a T sta nel piano degli strati, quindi lavora nel
  verso forte.
- **Prima di stampare tutto:** stampa un solo aggancio e un distanziale, provali nel profilo
  vero e poi correggi le quote.
