# Modulo di calcolo e cablaggio GPIO

## Modulo di calcolo

- **Raspberry Pi Zero 2 W** in una scatola stampata in due pezzi: base e coperchio
  (`pezzi/scatola_calcolo.stl`, `pezzi/coperchio_calcolo.stl`).
- **Dove sta:** sul fianco esterno del montante destro, lontano dai SiPM perché il Pi scalda
  (vedi `PROTOTIPI.md` di glacier-elettronica).
- **Come si stacca:** due alette, sopra e sotto, con linguetta a T nella scanalatura esterna
  e un pomello zigrinato M5 in un dado a T. Allentati i due pomelli, la scatola scorre
  lungo la scanalatura e si sfila dall'alto, dopo aver tolto il tappo del montante. Se la
  vuoi staccare senza togliere il tappo, al posto delle linguette continue servono chiavette a
  T "drop-in" che entrano di fronte e ruotano di 90°.
- **Raffreddamento:** ventola 30 × 30 × 10 mm a 5 V sotto il coperchio, con griglia di uscita
  sul coperchio e 7 feritoie di aspirazione sulla parete posteriore.
- **Accessi:**
  - mini-HDMI, micro-USB dati e micro-USB di alimentazione dalla parete anteriore;
  - microSD da una fessura sul fondo;
  - tutto il connettore GPIO 2×20 da una finestra nel coperchio.
- **Alimentazione del Pi:** alimentatore separato da 5 V, sulla presa PWR, come indicato in
  `PROTOTIPI.md`.

## Cablaggio GPIO → scheda a 3 canali

Il connettore è un **IDC 2×8** femmina, sui **pin 3–18** del Pi, con una cuffia stampata come
scarico della trazione (`pezzi/cuffia_gpio.stl`). Restano liberi i pin 1–2 e 19–40.

| Pin Pi | Segnale Pi | Cavo | Arriva a (scheda 3 canali) |
|---|---|---|---|
| 3 | GPIO2 / SDA | 3 poli, filo 2 | J6 pin 2 (SDA) |
| 5 | GPIO3 / SCL | 3 poli, filo 3 | J6 pin 3 (SCL) |
| 6 | GND | 3 poli, filo 1 | J6 pin 1 (GND) |
| 11 | GPIO17 | coassiale 1, centrale | LEMO **J104**: canale 1 |
| 13 | GPIO27 | coassiale 2, centrale | LEMO **J204**: canale 2 |
| 15 | GPIO22 | coassiale 3, centrale | LEMO **J304**: canale 3 |
| 16 | GPIO23 | coassiale 4, centrale | LEMO **J5**: coincidenza AND |
| 9 | GND | calze dei coassiali 1 e 2 | |
| 14 | GND | calze dei coassiali 3 e 4 | |
| 18 | GPIO24 | non collegato | riserva |

La ventola prende 5 V dal **pin 2** e GND dal **pin 20**, con due contatti Dupont singoli
all'interno della scatola.

Le uscite della scheda sono già a 0–3,3 V (buffer 74LVC1G17, 33 Ω in serie), quindi vanno
direttamente ai GPIO senza adattatori. Le pull-up dell'I²C sono quelle interne del Pi, come
previsto dalla scheda.

### Materiale

- 1 × connettore IDC 2×8 femmina, passo 2,54 mm, con contatti a crimpare (tipo Dupont o Harwin M20)
- 4 × spina **LEMO FFA.00.250** (serie 00, per RG174)
- RG174: 4 tratti da circa 60 cm
- cavo a 3 poli (0,14 mm²) da circa 50 cm + connettore femmina 1×3 passo 2,54 mm per J6
- guaina termorestringente e marcafili 1, 2, 3, AND

## Percorso dei cavi

I quattro coassiali escono dalle LEMO sul bordo anteriore della scheda, corrono affiancati sul
tavolo davanti al telaio e risalgono lungo il piede destro fino alla cuffia GPIO. Il cavo
I²C parte da J6, nell'angolo anteriore destro della scheda, e sale direttamente al modulo.
