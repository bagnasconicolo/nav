// =====================================================================
//  Tavola periodica a cubi espositivi - cubo parametrico
// ---------------------------------------------------------------------
//  Uso normale: cambiare solo Z (numero atomico) ed esportare.
//  Per testi personalizzati: Z = 0 e compilare i campi *_testo.
//  Esportazione in blocco: python3 strumenti/tavola.py esporta
//
//  Il cubo ha gli spigoli raggiati e dentro una nicchia curva su tutti
//  i lati, come un'alcova: il fondo del cubo è il piano espositivo e
//  davanti sale in curva fino alla fascia con la scritta. Si stampa
//  sdraiato (retro sul piatto, fronte in alto) senza supporti: le curve
//  stanno sul piano di stampa, scendono "a ciotola" verso il piatto o
//  non superano i 45°.
//
//  Sistema di riferimento (cubo "appeso"): X verso destra, Y dal fronte
//  (y = 0, aperto) verso il retro, Z verso l'alto.
// =====================================================================

include <elementi.scad>
// font incluse nel progetto (licenza OFL): non serve installarle
use <font/Syne-Bold.ttf>
use <font/Syne-SemiBold.ttf>
use <font/IBMPlexSans-Medium.ttf>
use <font/IBMPlexSans-SemiBold.ttf>
use <font/IBMPlexMono-Medium.ttf>
use <font/IBMPlexMono-SemiBold.ttf>

/* [Elemento] */
Z = 26;                     // numero atomico (0 = testi personalizzati)
numero_testo = "";          // se non vuoti, sostituiscono i dati della tabella
simbolo_testo = "";
nome_testo = "";
mostra_numero = true;
mostra_nome = false;        // il nome lo darà l'app: sul cubo bastano simbolo e numero

/* [Parte da generare] */
parte = "assemblato";       // [assemblato, corpo, testo, tappo, dima, corpo_appeso, sezione, info]

/* [Forma] */
lato = 60;                  // larghezza = altezza
profondita = 60;
raggio = 8;                 // spigoli esterni (davanti e lungo la profondità)
parete = 1.2;               // pareti e tetto (3 linee da 0,4)
fondo = 2.4;                // fondo = piano espositivo (ospita la scanalatura)
schiena = 1.6;              // parete posteriore (sta sul piatto)
raggio_fondo = 8;           // curva tra pareti e fondo della nicchia
raggio_bordo = 0.8;         // arrotondamento del bordo frontale esterno

/* [Fronte] */
cornice_sp = 2;             // spessore della lastra frontale
labbro = 1;                 // di quanto la cornice sporge dentro la nicchia
smusso_apertura = 0.6;      // smusso a 45° sul bordo dell'apertura
fascia_h = 10;              // fascia con i testi; dietro, il fondo sale in curva fin qui

/* [Tipografia] */
testo_modo = "rilievo";     // [rilievo, inciso]
testo_h = 0.6;              // altezza del rilievo / profondità dell'incisione
// Syne per il simbolo (display), IBM Plex per i testi, come museo.chicubo.it
// (in alternativa, nome in tondo: font_nome = "IBM Plex Sans:style=Medium",
//  nome_maiuscolo = false, spaziatura_nome = 1, h_nome = 3.4)
font_simbolo = "Syne:style=Bold";
font_nome = "IBM Plex Mono:style=SemiBold";
font_numero = "IBM Plex Mono:style=SemiBold";
// altezze delle MAIUSCOLE in mm (non il "size" di OpenSCAD).
// Sotto i 3 mm il tratto scende sotto i 0,45 mm: al limite per un ugello da 0,4.
h_simbolo = 6;
h_nome = 3;
h_numero = 4.5;            // si riduce da solo se non c'è spazio
nome_maiuscolo = true;      // nome in maiuscolo spaziato
spaziatura_nome = 1.12;
numero_cifre = 0;           // 3: 26 -> 026, come un numero di catalogo
margine_testo = 4;          // distanza dei testi dal bordo del cubo

/* [Riconoscimento con la fotocamera] */
codice = true;              // marker ArUco 4x4 sul fronte, ID = numero atomico
codice_cella = 1.1;         // lato di un quadratino (il marker è 6 x 6 celle)
codice_id = 0;              // ID per i cubi senza numero atomico (segnaposto)
margine_codice = 6;         // distanza del marker dal bordo destro

/* [Alleggerimento] */
// Finestre nelle pareti che confinano con un altro cubo: da fuori non si
// vedono. Su ogni confine se ne apre una sola (a destra e sopra), così
// tra due nicchie vicine resta sempre una parete piena.
finestre = true;
finestra_sopra = true;      // lo script le attiva solo se c'è un cubo sopra
finestra_dx = true;         // ... e a destra
finestra_margine = 4;       // distanza dagli spigoli raggiati
finestra_raggio = 5;

/* [Fissaggio al pannello] */
vite_d = 3.4;               // foro passante (M3)
svasatura_d = 6.9;          // vite M3 a testa svasata piana (ISO 10642)
mozzo_h = 3.5;              // sporgenza del mozzo della vite dalla schiena
tappo_h = 1.4;              // tappo a filo che copre la vite
spina = true;               // foro cieco per spina antirotazione nel pannello
spina_d = 4.2;              // spina Ø4
spina_prof = 4;
dima_pilota = 3.2;          // foro guida della dima per la vite
gioco = 0.15;

/* [Incastro tra cubi sovrapposti] */
lingua_sopra = true;        // linguetta sul lato alto (entra nel cubo sopra)
scanalatura_sotto = true;
lingua_w = 5;               // base della linguetta (fianchi a 45°)
lingua_h = 1;
lingua_gioco = 0.25;

/* [Nascosti] */
$fn = 64;
e = 0.01;

// ---------------------------------------------------------------------
// Dati dell'elemento
// ---------------------------------------------------------------------
dato = Z > 0 ? ELEMENTI[Z - 1] : ["", "", "", "", "", 0, 0];
function scegli(personale, tabella) = personale != "" ? personale : tabella;
function unisci(v, i = 0) = i >= len(v) ? "" : str(v[i], unisci(v, i + 1));
// maiuscolo (anche per le vocali accentate più comuni)
function car_maiuscolo(c) =
    let (o = ord(c)) (o >= 97 && o <= 122) || (o >= 224 && o <= 254 && o != 247) ? chr(o - 32) : c;
function maiuscolo(s) = unisci([for (c = s) car_maiuscolo(c)]);
function zeri(n, cifre) = len(str(n)) >= cifre ? str(n) : zeri(str("0", n), cifre);

T_NUMERO = mostra_numero ? scegli(numero_testo, Z > 0 ? zeri(dato[0], numero_cifre) : "") : "";
T_SIMBOLO = scegli(simbolo_testo, dato[1]);
T_NOME = !mostra_nome ? "" : nome_maiuscolo ? maiuscolo(scegli(nome_testo, dato[2])) : scegli(nome_testo, dato[2]);

// ---------------------------------------------------------------------
// Quote derivate
// ---------------------------------------------------------------------
y_fondo = profondita - schiena;                 // faccia interna della schiena
raggio_nicchia = max(raggio - parete, 0.5);     // angoli della nicchia, concentrici
// curva davanti: parte a 45° dal bordo della fascia e scende tangente al fondo
raggio_davanti = (fascia_h - fondo) / (1 - cos(45));
y_curva = cornice_sp + raggio_davanti * sin(45);   // dove finisce la curva
vite = [lato / 2, (fascia_h + lato - parete) / 2];
spina_pos = [vite[0] + svasatura_d / 2 + spina_d / 2 + 2.5, vite[1]];   // nello stesso mozzo

// ---------------------------------------------------------------------
// Profili nel piano frontale (X-Z) ed estrusioni lungo Y
// ---------------------------------------------------------------------
module rett_arrotondato(x0, z0, x1, z1, r) {
    r2 = max(min(r, (x1 - x0) / 2 - e, (z1 - z0) / 2 - e), e);
    translate([x0 + r2, z0 + r2]) offset(r = r2) square([x1 - x0 - 2 * r2, z1 - z0 - 2 * r2]);
}
// sagoma esterna del cubo, rientrata di "d"
module esterno_2d(d = 0) { rett_arrotondato(d, d, lato - d, lato - d, raggio - d); }
// sagoma della nicchia rientrata di "d", con il fondo a quota "zb"
module nicchia_2d(d = 0, zb = fondo) {
    rett_arrotondato(parete + d, zb + d, lato - parete - d, lato - parete - d, raggio_nicchia - d);
}
// estrude una sagoma X-Z lungo Y, da y0 per una lunghezza l
module lungo_y(y0, l) { translate([0, y0 + l, 0]) rotate([90, 0, 0]) linear_extrude(l) children(); }

// ---------------------------------------------------------------------
// Corpo
// ---------------------------------------------------------------------
module pieno() {
    r = raggio_bordo;
    hull() {
        // bordo frontale arrotondato: tra due cubi diventa una fuga d'ombra
        for (a = [0 : 15 : 90]) lungo_y(r - r * cos(a), e) esterno_2d(r - r * sin(a));
        lungo_y(r, profondita - r) esterno_2d();
    }
}

module nicchia() {
    rf = raggio_fondo;
    ra = raggio_davanti;
    hull() {
        // davanti: il fondo sale in curva fino alla fascia (massimo 45°: stampabile)
        for (f = [45 : -5 : 0])
            lungo_y(cornice_sp + ra * (sin(45) - sin(f)), e) nicchia_2d(0, fondo + ra * (1 - cos(f)));
        lungo_y(y_curva, y_fondo - rf - y_curva) nicchia_2d();
        // raccordo curvo verso il fondo, su tutti e quattro i lati
        for (a = [0 : 10 : 90]) lungo_y(y_fondo - rf + rf * sin(a) - e, e) nicchia_2d(rf - rf * cos(a));
    }
}

module apertura() {
    s = smusso_apertura;
    lungo_y(-1, cornice_sp + 2) nicchia_2d(labbro, fascia_h);
    hull() {
        lungo_y(-e, e) nicchia_2d(labbro - s, fascia_h);
        lungo_y(s, e) nicchia_2d(labbro, fascia_h);
    }
}

// sotto la curva davanti resta un cuneo: lo svuoto, lasciando un guscio di
// "parete" sotto la curva e il fondo pieno (porta la scanalatura). Unione di
// tratti, non un unico hull: la curva è concava vista da sotto.
module cuneo_vuoto() {
    ra = raggio_davanti;
    function zc(f) = fondo + ra * (1 - cos(f)) - parete;
    function yc(f) = cornice_sp + ra * (sin(45) - sin(f));
    passi = [for (f = [45 : -5 : 0]) if (zc(f) > fondo + 1) f];
    for (i = [0 : len(passi) - 2])
        hull() for (f = [passi[i], passi[i + 1]])
            lungo_y(i == 0 && f == passi[0] ? cornice_sp : yc(f), e) intersection() {
                esterno_2d(parete);
                translate([0, fondo]) square([lato, zc(f) - fondo]);
            }
}

module finestre() {
    m = finestra_margine;
    y0 = cornice_sp + 6;
    y1 = y_fondo - raggio_fondo - 2;
    if (finestra_dx)
        translate([lato - parete - 1, 0, 0]) rotate([90, 0, 90]) linear_extrude(parete + 2)
            rett_arrotondato(y0, raggio + m, y1, lato - raggio - m, finestra_raggio);
    // sopra: due finestre, la striscia centrale porta la linguetta
    if (finestra_sopra)
        for (x = [[raggio + m, lato / 2 - lingua_w / 2 - 3], [lato / 2 + lingua_w / 2 + 3, lato - raggio - m]])
            translate([0, 0, lato - parete - 1]) linear_extrude(parete + 2)
                rett_arrotondato(x[0], y0, x[1], y1, finestra_raggio);
}

// mozzo al centro della schiena: vite al centro, spina accanto (foro cieco dal retro)
module mozzo() {
    hull() {
        translate([vite[0], y_fondo + e, vite[1]]) rotate([90, 0, 0])
            cylinder(d = svasatura_d + 5, h = mozzo_h + e);
        if (spina) translate([spina_pos[0], y_fondo + e, spina_pos[1]]) rotate([90, 0, 0])
            cylinder(d = spina_d + 3, h = mozzo_h + e);
    }
}

function trapezio(w, h, g = 0) = [
    [-w / 2 - g, -e], [w / 2 + g, -e],
    [w / 2 - h + g, h + g], [-w / 2 + h - g, h + g]];

module linguetta() {
    if (lingua_sopra)
        lungo_y(raggio_bordo, profondita - raggio_bordo) translate([lato / 2, lato]) polygon(trapezio(lingua_w, lingua_h));
}

module scanalatura() {
    if (scanalatura_sotto)
        lungo_y(-1, profondita + 2) translate([lato / 2, 0]) polygon(trapezio(lingua_w, lingua_h, lingua_gioco));
}

module fori() {
    // vite a testa svasata: cono che si allarga verso il fronte (verso l'alto in
    // stampa, niente supporti) e sopra la sede del tappo
    y0 = y_fondo - mozzo_h;
    translate([vite[0], 0, vite[1]]) rotate([-90, 0, 0]) {
        translate([0, 0, y0 - 1]) cylinder(d = vite_d, h = profondita);
        translate([0, 0, y0 - 1]) cylinder(d = svasatura_d + 0.4, h = tappo_h + 1);
        translate([0, 0, y0 + tappo_h - e])
            cylinder(d1 = svasatura_d, d2 = vite_d, h = (svasatura_d - vite_d) / 2);
    }
    // tacca per sollevare il tappo con la punta di un cacciavite
    translate([vite[0] + svasatura_d / 2 - 0.4, y0 - 1, vite[1] - 1.2]) cube([2, tappo_h + 1, 2.4]);
    if (spina)
        translate([spina_pos[0], profondita - spina_prof, spina_pos[1]]) rotate([-90, 0, 0])
            cylinder(d = spina_d, h = spina_prof + 1);
}

// ---------------------------------------------------------------------
// Tipografia (di serie: solo simbolo e numero, sulla stessa linea di base)
//   | Fe                                  26 |   <- Syne / Plex Mono
// Con mostra_nome il numero sale e allinea la cima a quella del simbolo:
//   |                                     26 |
//   | Fe                               FERRO |
// Simbolo centrato nella fascia, margini uguali in basso e a sinistra.
// ---------------------------------------------------------------------
// OpenSCAD dimensiona i testi con "size", che non è l'altezza delle maiuscole:
// questi rapporti (misurati sulle font incluse) convertono tra le due.
K_CAP_SYNE = 0.90;
K_CAP_PLEX = 0.97;
// larghezza media di un carattere in rapporto a "size" (misurata): serve solo
// a ridurre i nomi lunghi, OpenSCAD 2021 non sa misurare un testo.
function sotto(s, i, n) = unisci([for (j = [i : i + n - 1]) s[j]]);
function contiene(s, t, i = 0) =
    i > len(s) - len(t) ? false : sotto(s, i, len(t)) == t ? true : contiene(s, t, i + 1);
function k_larghezza(font, maiuscolo) =
    contiene(font, "Mono") ? 0.81 : contiene(font, "Syne") ? 0.95 : maiuscolo ? 0.86 : 0.71;
function adatta(t, dim, k, max_w) = len(t) == 0 ? dim : min(dim, max_w / (len(t) * k));

module testi_2d() {
    s_sim = h_simbolo / K_CAP_SYNE;
    utile = fascia_h + labbro - smusso_apertura;
    base = (utile - h_simbolo) / 2;
    sx = margine_testo;
    dx = lato - margine_testo;
    w_sim = len(T_SIMBOLO) * s_sim * k_larghezza(font_simbolo, false);
    s_nome = adatta(T_NOME, h_nome / K_CAP_PLEX, k_larghezza(font_nome, nome_maiuscolo) * spaziatura_nome,
                    dx - sx - w_sim - 6);
    translate([sx, base]) text(T_SIMBOLO, size = s_sim, font = font_simbolo);
    // marker ArUco all'estremità destra, centrato nella fascia; il numero gli sta accanto
    lato_codice = 6 * codice_cella;
    dx_num = codice ? lato - margine_codice - lato_codice - 2.2 : dx;
    if (codice) translate([lato - margine_codice - lato_codice, (utile - lato_codice) / 2]) marker_2d();
    // il numero si riduce da solo se non ci sta (es. "89–103" dei segnaposto)
    s_num = adatta(T_NUMERO, h_numero / K_CAP_PLEX, k_larghezza(font_numero, false), dx_num - sx - w_sim - 3);
    // senza nome il numero scende sulla linea di base del simbolo
    translate([dx_num, len(T_NOME) > 0 ? base + h_simbolo - s_num * K_CAP_PLEX : base])
        text(T_NUMERO, size = s_num, font = font_numero, halign = "right");
    translate([dx, base])
        text(T_NOME, size = s_nome, font = font_nome, halign = "right", spacing = spaziatura_nome);
}

// celle nere del marker (in rilievo, nel colore del testo); il chiaro è il fronte
module marker_2d() {
    bit = ARUCO[Z > 0 ? Z : codice_id];
    c = codice_cella;
    for (r = [0 : 5], k = [0 : 5]) if (bit[r * 6 + k] == 0)
        translate([k * c - 0.005, (5 - r) * c - 0.005]) square(c + 0.01);
}

module testi(h) { rotate([90, 0, 0]) linear_extrude(h) testi_2d(); }

module corpo() {
    difference() {
        union() {
            difference() { pieno(); nicchia(); apertura(); cuneo_vuoto(); if (finestre) finestre(); }
            mozzo();
            linguetta();
            if (testo_modo == "rilievo") testi(testo_h);
        }
        scanalatura();
        fori();
        if (testo_modo == "inciso") translate([0, testo_h, 0]) testi(testo_h + 1);
    }
}

// tappo a filo sulla vite (stesso colore del corpo)
module tappo() {
    cylinder(d = svasatura_d + 0.4 - 2 * gioco, h = tappo_h);
}

// ---------------------------------------------------------------------
// Dima per forare il pannello (si appoggia al pannello, vista frontale)
// ---------------------------------------------------------------------
module dima() {
    difference() {
        union() {
            linear_extrude(2) difference() { esterno_2d(); esterno_2d(12); }
            for (a = [45, 135, 225, 315]) translate([lato / 2, lato / 2, 0]) rotate(a)
                translate([0, -4, 0]) cube([lato * 0.56, 8, 2]);
            translate([vite[0], vite[1], 0]) cylinder(d = 12, h = 10);
            if (spina) translate([spina_pos[0], spina_pos[1], 0]) cylinder(d = 12, h = 10);
        }
        translate([vite[0], vite[1], -1]) cylinder(d = dima_pilota, h = 20);
        if (spina) translate([spina_pos[0], spina_pos[1], -1]) cylinder(d = spina_d - 0.2, h = 20);
        translate([lato / 2, lato - 9.5, 1.2]) linear_extrude(5)
            text("ALTO", size = 4, font = font_nome, halign = "center");
    }
}

// ---------------------------------------------------------------------
// Uscita
// ---------------------------------------------------------------------
module per_stampa() {
    // sdraiato: retro sul piatto, fronte in alto
    translate([0, 0, profondita]) rotate([-90, 0, 0]) children();
}

if (parte == "corpo") per_stampa() corpo();
else if (parte == "tappo") tappo();
else if (parte == "dima") dima();
// solo i testi, già nella posizione di stampa: per assegnare loro un altro filamento
else if (parte == "testo") per_stampa() testi(testo_h);
// posizione "appesa", per anteprime e montaggi
else if (parte == "corpo_appeso") corpo();
else if (parte == "sezione") intersection() {
    corpo();
    translate([lato / 2, -10, -10]) cube([lato, profondita + 20, lato + 20]);
}
else if (parte == "info")
    echo(VITE = vite, SPINA = spina_pos, LATO = lato, PROFONDITA = profondita, CORNICE = cornice_sp,
         TAPPO = [y_fondo - mozzo_h, svasatura_d + 0.4 - 2 * gioco, tappo_h]);
else color("#e9e6df") corpo();
