# Cablaggio e moduli elettronici (v14)

Il sistema segue l'architettura di glacier-elettronica (ramo `claude/gallant-feynman-h18ciy`,
`docs/SISTEMA_schemi_PCB_preventivo.pdf`):

- **rivelatore a 3 canali** (`hardware/variante_3ch`), sul modulo scheda davanti al telaio;
- **scatolina di acquisizione** (`hardware/moduli/acquisizione`): Pico 2, 4 ingressi LEMO, uscita PPS,
  GPS e hub I²C; sta in una scatola stampata sul montante destro;
- **Raspberry Pi Zero 2 W** nella scatola con ventola sul montante sinistro;
- **modulo meteo** (`hardware/moduli/meteo`, SHT45 + LPS22HH) su un supporto stampato, sul montante
  sinistro sotto lo Zero.

Rispetto alla v13 non c'è più il cablaggio sui GPIO dello Zero: gli impulsi li cattura il Pico, che
passa i dati allo Zero via USB.

## Scatola di acquisizione (montante destro)

- **Contenuto:** la scheda del Pico (105 × 70 mm) su 4 borchie con inserti M3 e, sotto, il GPS NEO-M9N
  (breakout SparkFun GPS-17285, 40,6 × 36,8 mm) su 4 borchie da 10 mm.
- **Fronte:** le 5 prese LEMO a gomito escono dalla parete in colonna. Dall'alto: ingressi 1, 2, 3,
  AND e uscita PPS, con le scritte incise accanto.
- **Retro:** una feritoia lascia accessibili tutte le porte I²C dell'hub: 2 KK (porte 0 e 1, verso i
  rivelatori) e 6 Qwiic (porte 2–7).
- **Sopra:** passa la micro-USB del Pico.
- **Sotto:** esce l'SMA del GPS.
- **Fissaggio e apertura:** la scatola si fissa come lo Zero, con due pomelli M5 in dadi a T nella cava
  esterna del montante. Il coperchio ha 4 viti M3 svasate e feritoie sopra il Pico, che lasciano
  vedere il LED di attività.

## Collegamenti

| Da | A | Cavo | Percorso |
|---|---|---|---|
| Barre 1–3 | J101 / J201 / J301 della scheda | RG174 con Molex KK 254 a 2 poli (segnale + bias sulla calza) | lungo il fronte dei montanti, come nella v13 |
| LEMO J104, J204, J304 della scheda | ingressi 1, 2, 3 della scatola di acquisizione | LEMO 00 – LEMO 00, RG174, circa 60 cm, tutti della stessa lunghezza | sul tavolo davanti al telaio, poi su lungo il fronte della scatola |
| LEMO J5 (AND) della scheda | ingresso AND | come sopra | come sopra |
| J6 della scheda (I²C, KK 3 poli: 1 GND, 2 SDA, 3 SCL) | porta 0 dell'hub (KK 3 poli) | 3 poli, circa 70 cm | sotto la scheda, sotto la traversa, dentro la sua cava posteriore, su per il retro del montante destro, nella feritoia |
| Porta 2 dell'hub (Qwiic) | modulo meteo (Qwiic J1) | Qwiic 500 mm | dentro la cava posteriore della traversa e su per il retro del montante sinistro |
| USB del Pico (dall'alto) | USB dati dello Zero (non PWR) | micro-USB – micro-USB OTG, circa 70 cm | sopra la scatola, giù per il retro del montante destro, nella cava della traversa, su per il montante sinistro |
| PWR dello Zero | alimentatore 5 V 2,5 A | micro-USB | dal retro, sul tavolo |
| USB-C J7 della scheda | alimentatore 5 V | USB-C | dal bordo posteriore della scheda, sotto la traversa, verso il retro |
| SMA del GPS | antenna attiva (cavo 3–5 m) | RG174 con SMA | sotto la scatola, verso la finestra |

All'interno della scatola di acquisizione, 6 cavetti Dupont femmina-femmina collegano la strip J6 del
Pico (1 5V, 2 3V3, 3 GND, 4 TX, 5 RX, 6 PPS) al connettore del GPS.

I cavi che attraversano il telaio corrono **dentro la cava posteriore della traversa**: si infilano
dall'apertura da 6 mm e, se serve, si chiudono con un profilo copricava. Escono vicino ai piedi e
salgono lungo il retro dei montanti. Sul tavolo dietro il rivelatore restano solo i cavi di
alimentazione e quello dell'antenna.

## Alimentazione

- **Rivelatore:** 5 V da un alimentatore USB-C su J7, ingresso protetto da fusibile, TVS e MOSFET contro
  l'inversione. J3 resta per l'alimentatore da banco, solo a 5 V, e nel montaggio normale non si usa.
- **Zero 2 W:** alimentatore separato da 5 V 2,5 A. Lo Zero alimenta poi via USB la scatolina, il GPS
  e il modulo meteo.
- **Masse:** rivelatore e scatolina hanno la massa in comune attraverso le calze dei LEMO e il GND
  del cavo I²C.

## Materiale

- 4 cavi LEMO 00 – 00, lunghi uguali (un metro in più vale 5 ns); uno in più per l'uscita PPS
  verso l'oscilloscopio
- 1 cavo a 3 poli con 2 connettori Molex 22-01-3037 (contatti 08-50-0114)
- 1 cavo Qwiic da 500 mm (SparkFun PRT-14429)
- 1 cavo micro-USB – micro-USB OTG da circa 70 cm
- 6 cavetti Dupont femmina-femmina da 10 cm
- antenna GPS attiva SMA con cavo da 3–5 m (es. Adafruit 960)
- alimentatori 5 V: USB-C per il rivelatore, micro-USB 2,5 A per lo Zero
