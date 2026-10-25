// =====================================================================
//  Tavola periodica a cubi espositivi - cubo parametrico
// ---------------------------------------------------------------------
//  Uso normale: cambiare solo Z (numero atomico) ed esportare.
//  Per testi personalizzati: Z = 0 e compilare i campi *_testo.
//  Esportazione in blocco: python3 strumenti/tavola.py esporta
//
//  Due pezzi per elemento:
//   - il cubo (guscio con cornice e targhetta), stampato sdraiato:
//     retro sul piatto, fronte con la scritta in alto, senza supporti;
//   - il fondale curvo, uguale per tutti, da stampare in un colore a
//     contrasto: fa da piano espositivo e nasconde la vite.
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

/* [Parte da generare] */
parte = "assemblato";       // [assemblato, corpo, testo, fondale, dima, corpo_appeso, fondale_appeso, sezione, info]

/* [Dimensioni] */
lato = 100;                 // larghezza = altezza
profondita = 100;
parete = 1.6;               // pareti laterali (4 linee da 0,4)
fondo = 2;                  // parete inferiore
cielo = 2;                  // parete superiore
schiena = 2;                // parete posteriore (sta sul piatto)
raggio_bordo = 1.2;         // arrotondamento del bordo frontale esterno:
                            // tra due cubi accostati diventa una fuga d'ombra

/* [Cornice] */
cornice_sp = 3;             // spessore (profondità) della cornice frontale
cornice = 3;                // larghezza della cornice su lati e sopra
fascia_h = 16;              // fascia bassa con i testi
raggio_apertura = 3;        // raggio degli angoli dell'apertura
smusso_apertura = 0.8;      // smusso a 45° sul bordo dell'apertura

/* [Tipografia] */
testo_modo = "rilievo";     // [rilievo, inciso]
testo_h = 0.6;              // altezza del rilievo / profondità dell'incisione
// Syne per il simbolo (display), IBM Plex per i testi, come museo.chicubo.it
font_simbolo = "Syne:style=Bold";
// (in alternativa, nome in tondo: font_nome = "IBM Plex Sans:style=Medium",
//  nome_maiuscolo = false, spaziatura_nome = 1, h_nome = 3.6)
font_nome = "IBM Plex Mono:style=SemiBold";
font_numero = "IBM Plex Mono:style=SemiBold";
// altezze delle MAIUSCOLE in mm (non il "size" di OpenSCAD).
// Sotto i 3 mm il tratto scende sotto i 0,45 mm: al limite per un ugello da 0,4.
h_simbolo = 8;
h_nome = 3;
h_numero = 3;
nome_maiuscolo = true;      // nome in maiuscolo spaziato
spaziatura_nome = 1.12;
numero_cifre = 0;           // 3: 26 -> 026, come un numero di catalogo
margine_testo = 4;          // distanza dei testi dai bordi della cornice

/* [Fondale curvo] */
fondale_sp = 1.6;               // 4 linee da 0,4
fondale_raggio = 24;        // raggio della curva tra piano e fondo
fondale_distanza = 2.5;     // distacco dalla schiena (lo spazio della testa della vite)
gioco = 0.3;

/* [Fissaggio al pannello] */
vite_d = 4.5;               // foro passante (M4)
svasatura_d = 9.2;          // vite M4 a testa svasata piana (ISO 10642)
spina = true;               // foro cieco per spina antirotazione nel pannello
spina_d = 6.2;
spina_prof = 5;
dima_pilota = 3.2;          // foro guida della dima per la vite

/* [Incastri tra cubi] */
lingua_sopra = true;        // linguetta sul lato alto (entra nel cubo sopra)
scanalatura_sotto = true;
lingua_dx = true;           // linguetta sul lato destro
scanalatura_sx = true;
lingua_w = 5;               // base della linguetta (fianchi a 45°)
lingua_h = 1.2;
lingua_gioco = 0.25;

/* [Nascosti] */
$fn = 64;
e = 0.01;

// ---------------------------------------------------------------------
// Dati dell'elemento
// ---------------------------------------------------------------------
dato = Z > 0 ? ELEMENTI[Z - 1] : ["", "", "", "", "", 0, 0];
function scegli(personale, tabella) = personale != "" ? personale : tabella;
// maiuscolo (anche per le vocali accentate più comuni)
function car_maiuscolo(c) =
    let (o = ord(c)) (o >= 97 && o <= 122) || (o >= 224 && o <= 254 && o != 247) ? chr(o - 32) : c;
function unisci(v, i = 0) = i >= len(v) ? "" : str(v[i], unisci(v, i + 1));
function maiuscolo(s) = unisci([for (c = s) car_maiuscolo(c)]);

function zeri(n, cifre) = len(str(n)) >= cifre ? str(n) : zeri(str("0", n), cifre);
T_NUMERO = mostra_numero ? scegli(numero_testo, Z > 0 ? zeri(dato[0], numero_cifre) : "") : "";
T_SIMBOLO = scegli(simbolo_testo, dato[1]);
T_NOME = nome_maiuscolo ? maiuscolo(scegli(nome_testo, dato[2])) : scegli(nome_testo, dato[2]);

// ---------------------------------------------------------------------
// Quote derivate
// ---------------------------------------------------------------------
z_piano = fascia_h;                            // piano espositivo a filo della fascia
z_appoggio = z_piano - fondale_sp;             // dove appoggia il fondale davanti
y_fondo = profondita - schiena;                // faccia interna della schiena
vite = [lato / 2, lato / 2];                   // vite al centro, dietro il fondale
spina_pos = [parete + 9, fondo + 6];           // spina nell'angolo basso, sotto il piano
z_lingua_lato = fondo + (z_appoggio - fondo) / 2;

// ---------------------------------------------------------------------
// Utilità
// ---------------------------------------------------------------------
// Prisma da un poligono nel piano Y-Z, esteso lungo X da x0 a x1
module prisma_yz(x0, x1) {
    translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();
}
// Profilo trapezoidale della linguetta (base sul piano, punta verso +v)
function trapezio(w, h, g = 0) = [
    [-w / 2 - g, -e], [w / 2 + g, -e],
    [w / 2 - h + g, h + g], [-w / 2 + h - g, h + g]];

module rett_arrotondato(w, h, r) {
    translate([r, r]) offset(r = r) square([w - 2 * r, h - 2 * r]);
}

// ---------------------------------------------------------------------
// Guscio
// ---------------------------------------------------------------------
module guscio_pieno() {
    r = raggio_bordo;
    hull() {
        // bordo frontale a quarto di cerchio
        for (a = [0 : 15 : 90]) {
            rientro = r - r * sin(a);
            translate([rientro, r - r * cos(a), rientro])
                cube([lato - 2 * rientro, e, lato - 2 * rientro]);
        }
        translate([0, r, 0]) cube([lato, profondita - r, lato]);
    }
}

module apertura() {
    // luce della cornice, con angoli raggiati e smusso a 45° sul fronte
    w = lato - 2 * cornice;
    h = lato - fascia_h - cornice;
    s = smusso_apertura;
    translate([cornice, 0, fascia_h]) rotate([90, 0, 0]) {
        translate([0, 0, -cornice_sp - 1]) linear_extrude(cornice_sp + 2)
            rett_arrotondato(w, h, raggio_apertura);
        hull() {
            translate([0, 0, -s]) linear_extrude(e) rett_arrotondato(w, h, raggio_apertura);
            translate([-s, -s, e]) linear_extrude(e) rett_arrotondato(w + 2 * s, h + 2 * s, raggio_apertura + s);
        }
    }
}

module corpo_guscio() {
    difference() {
        guscio_pieno();
        // cavità interna
        translate([parete, cornice_sp, fondo])
            cube([lato - 2 * parete, profondita - schiena - cornice_sp, lato - fondo - cielo]);
        apertura();
    }
    // dietro la fascia: lastra a 45° che regge il bordo del fondale.
    // Resta cava dietro: si stampa senza supporti e non spreca materiale.
    y_b = cornice_sp + 2;
    t = 1.6 * sqrt(2);
    prisma_yz(parete - e, lato - parete + e)
        polygon([[y_b - t - 1, z_appoggio], [y_b, z_appoggio],
                 [y_b + z_appoggio - fondo, fondo - e], [y_b + z_appoggio - fondo - t, fondo - e]]);
}

// rinforzi nascosti sotto il piano, dove le pareti ospitano scanalature e spina
module rinforzi() {
    y0 = cornice_sp;
    y1 = y_fondo + e;
    if (scanalatura_sx)
        translate([parete - e, y0, z_lingua_lato - lingua_w / 2 - 1.5])
            cube([1.6, y1 - y0, lingua_w + 3]);
    if (scanalatura_sotto)
        translate([lato / 2 - lingua_w / 2 - 2, y0, fondo - e]) cube([lingua_w + 4, y1 - y0, 1.6]);
    // mozzo della vite: porta la svasatura e regge il fondale
    translate([vite[0], y_fondo + e, vite[1]]) rotate([90, 0, 0])
        cylinder(d = 16, h = fondale_distanza + e);
    // due appoggi in alto per il fondale
    for (x = [lato * 0.2, lato * 0.8])
        translate([x, y_fondo + e, lato - cielo - 14]) rotate([90, 0, 0])
            cylinder(d = 8, h = fondale_distanza + e);
    if (spina)
        translate([spina_pos[0], y_fondo + e, spina_pos[1]]) rotate([90, 0, 0])
            cylinder(d = 11, h = spina_prof - schiena + 1.2);
}

module linguette() {
    if (lingua_sopra)
        translate([lato / 2, raggio_bordo, lato]) rotate([-90, 0, 0])
            linear_extrude(profondita - raggio_bordo)
                mirror([0, 1, 0]) polygon(trapezio(lingua_w, lingua_h));
    if (lingua_dx)
        translate([lato, raggio_bordo, z_lingua_lato]) rotate([-90, 0, 0])
            linear_extrude(profondita - raggio_bordo)
                rotate(90) mirror([0, 1, 0]) polygon(trapezio(lingua_w, lingua_h));
}

module scanalature() {
    if (scanalatura_sotto)
        translate([lato / 2, -1, 0]) rotate([-90, 0, 0])
            linear_extrude(profondita + 2)
                mirror([0, 1, 0]) polygon(trapezio(lingua_w, lingua_h, lingua_gioco));
    if (scanalatura_sx)
        translate([0, -1, z_lingua_lato]) rotate([-90, 0, 0])
            linear_extrude(profondita + 2)
                rotate(90) mirror([0, 1, 0]) polygon(trapezio(lingua_w, lingua_h, lingua_gioco));
}

module fori_fissaggio() {
    // vite a testa svasata, a filo del mozzo. Il cono si allarga verso il
    // fronte, cioè verso l'alto in stampa: niente supporti.
    y_mozzo = y_fondo - fondale_distanza;
    translate([vite[0], 0, vite[1]]) rotate([-90, 0, 0]) {
        translate([0, 0, y_mozzo - 1]) cylinder(d = vite_d, h = profondita);
        translate([0, 0, y_mozzo - 1]) cylinder(d = svasatura_d, h = 1 + e);
        translate([0, 0, y_mozzo]) cylinder(d1 = svasatura_d, d2 = vite_d, h = (svasatura_d - vite_d) / 2);
    }
    // spina antirotazione: foro cieco dal retro
    if (spina)
        translate([spina_pos[0], profondita - spina_prof, spina_pos[1]]) rotate([-90, 0, 0])
            cylinder(d = spina_d, h = spina_prof + 1);
}

// ---------------------------------------------------------------------
// Tipografia
//   |                                     26 |  <- Plex Mono, cima allineata al simbolo
//   | Fe                               FERRO |  <- Syne / Plex Mono, stessa linea di base
// Margini uguali in basso e a sinistra; simbolo centrato nella fascia.
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
    s_num = h_numero / K_CAP_PLEX;
    utile = fascia_h - smusso_apertura;
    base = (utile - h_simbolo) / 2;
    sx = cornice + margine_testo - 2;
    dx = lato - cornice - margine_testo + 2;
    w_sim = len(T_SIMBOLO) * s_sim * k_larghezza(font_simbolo, false);
    s_nome = adatta(T_NOME, h_nome / K_CAP_PLEX, k_larghezza(font_nome, nome_maiuscolo) * spaziatura_nome,
                    dx - sx - w_sim - 8);
    translate([sx, base]) text(T_SIMBOLO, size = s_sim, font = font_simbolo);
    translate([dx, base + h_simbolo - h_numero])
        text(T_NUMERO, size = s_num, font = font_numero, halign = "right");
    translate([dx, base])
        text(T_NOME, size = s_nome, font = font_nome, halign = "right", spacing = spaziatura_nome);
}

module testi(h) {
    rotate([90, 0, 0]) linear_extrude(h) testi_2d();
}

module corpo() {
    difference() {
        union() {
            corpo_guscio();
            rinforzi();
            linguette();
            if (testo_modo == "rilievo") testi(testo_h);
        }
        scanalature();
        fori_fissaggio();
        if (testo_modo == "inciso") translate([0, testo_h, 0]) testi(testo_h + 1);
    }
}

// ---------------------------------------------------------------------
// Fondale curvo: piano espositivo + curva + fondo, in un pezzo solo.
// Si infila dal fronte dopo aver avvitato il cubo e nasconde la vite.
// ---------------------------------------------------------------------
module profilo_fondale() {
    t = fondale_sp;
    R = fondale_raggio;
    y0 = cornice_sp + gioco;                    // bordo anteriore del piano
    yb = y_fondo - fondale_distanza - gioco;    // faccia posteriore del fondo
    cy = yb - t - R;                            // centro della curva
    cz = z_piano + R;
    zt = lato - cielo - gioco;                  // bordo superiore
    // piano
    translate([y0, z_piano - t]) square([cy - y0, t]);
    // fondo
    translate([yb - t, cz]) square([t, zt - cz]);
    // curva
    intersection() {
        difference() {
            translate([cy, cz]) circle(r = R + t, $fn = 160);
            translate([cy, cz]) circle(r = R, $fn = 160);
        }
        translate([cy, cz - R - t]) square([R + t, R + t]);
    }
    // gamba centrale sotto il piano
    translate([(y0 + cy) / 2 - t / 2, fondo + gioco]) square([t, z_piano - t - fondo - gioco + e]);
}

module fondale() {
    prisma_yz(parete + gioco, lato - parete - gioco) profilo_fondale();
}

// ---------------------------------------------------------------------
// Dima per forare il pannello (si appoggia al pannello, vista frontale)
// ---------------------------------------------------------------------
module dima() {
    difference() {
        union() {
            difference() {
                cube([lato, lato, 2]);
                translate([16, 16, -1]) cube([lato - 32, lato - 32, 4]);
            }
            // bracci verso la vite al centro
            for (a = [45, 135, 225, 315]) translate([lato / 2, lato / 2, 0]) rotate(a)
                translate([0, -4, 0]) cube([lato * 0.66, 8, 2]);
            translate([vite[0], vite[1], 0]) cylinder(d = 12, h = 10);
            if (spina) translate([spina_pos[0], spina_pos[1], 0]) cylinder(d = 12, h = 10);
        }
        translate([vite[0], vite[1], -1]) cylinder(d = dima_pilota, h = 20);
        if (spina) translate([spina_pos[0], spina_pos[1], -1]) cylinder(d = spina_d - 0.2, h = 20);
        translate([lato / 2, lato - 11, 1.2]) linear_extrude(5)
            text("ALTO", size = 5, font = font_nome, halign = "center");
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
// fondale in piedi sul suo profilo: niente supporti
else if (parte == "fondale") fondale_in_piedi();
else if (parte == "dima") dima();
// solo i testi, già nella posizione di stampa: per assegnare loro un altro filamento
else if (parte == "testo") per_stampa() testi(testo_h);
// stessi pezzi nella posizione "appesa", per anteprime e montaggi
else if (parte == "corpo_appeso") corpo();
else if (parte == "fondale_appeso") fondale();
else if (parte == "sezione") intersection() {
    union() { corpo(); fondale(); }
    translate([lato / 2, -10, -10]) cube([lato, profondita + 20, lato + 20]);
}
else if (parte == "info")
    echo(VITE = vite, SPINA = spina_pos, LATO = lato, PROFONDITA = profondita, CORNICE = cornice_sp);
else {
    color("#e9e6df") corpo();
    color("#2f3133") fondale();
}

module fondale_in_piedi() {
    // il profilo Y-Z diventa la base sul piatto, l'estrusione va in altezza
    linear_extrude(lato - 2 * parete - 2 * gioco) profilo_fondale();
}
