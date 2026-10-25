// =====================================================================
//  Tavola periodica a cubi espositivi - cubo parametrico
// ---------------------------------------------------------------------
//  Uso normale: cambiare solo Z (numero atomico) ed esportare.
//  Per testi personalizzati: Z = 0 e compilare i campi *_testo.
//  Esportazione in blocco: python3 strumenti/tavola.py esporta
//
//  Sistema di riferimento (cubo "appeso"): X verso destra, Y dal fronte
//  (y = 0, aperto) verso il retro, Z verso l'alto. L'esportazione ruota
//  il pezzo con il retro sul piatto e il fronte (con il testo) in alto.
// =====================================================================

include <elementi.scad>

/* [Elemento] */
Z = 26;                     // numero atomico (0 = testi personalizzati)
numero_testo = "";          // se non vuoti, sostituiscono i dati della tabella
simbolo_testo = "";
nome_testo = "";
massa_testo = "";

/* [Parte da generare] */
parte = "assemblato";       // [assemblato, corpo, pavimento, dima, testo, corpo_appeso, pavimento_appeso, sezione, info]

/* [Dimensioni] */
lato = 100;                 // larghezza = altezza
profondita = 100;
parete = 2;                 // pareti laterali
fondo = 2.4;                // parete inferiore
cielo = 2.4;                // parete superiore
schiena = 2.4;              // parete posteriore
smusso = 0.8;               // smusso sugli spigoli anteriori

/* [Cornice e targhetta] */
cornice_sp = 4;             // spessore della cornice frontale
cornice_lato = 4;           // larghezza della cornice ai lati
visiera_h = 15;             // fascia alta: nasconde il LED
fascia_h = 24;              // fascia bassa con i testi (= quota del piano espositivo)
testo_modo = "rilievo";     // [rilievo, inciso]
testo_h = 0.6;              // altezza del rilievo / profondità dell'incisione
font_simbolo = "Inter:style=Bold";
font_testo = "Inter:style=SemiBold";
smusso_apertura = 1.5;      // smusso a 45° sul bordo dell'apertura
// dimensioni massime: si riducono da sole se il testo è lungo
dim_simbolo = 11.5;
dim_numero = 4.4;
dim_nome = 5.5;
dim_massa = 4;
margine_testo = 4;

/* [Illuminazione] */
led = true;                 // canale per striscia LED sotto la visiera, inclinato a 45°
led_larghezza = 10.5;       // striscia da 10 mm (8 mm -> 8.5)
led_profondita = 2;
cavo_d = 4;                 // tunnel cavi nello spigolo alto destro, esce dal retro
raccordo = 10;              // smusso interno negli spigoli alti (contiene il tunnel)
foro_vano = 8;              // foro passacavi del vano tecnico (0 = niente)

/* [Vano tecnico e pavimento] */
costola = 3;                // appoggi laterali del pavimento
battuta = 3;                // appoggio anteriore del pavimento
pav_sp = 2.4;               // spessore del pavimento estraibile
gioco = 0.3;
tacca_dito = 9;             // raggio della tacca per sollevare il pavimento

/* [Fissaggio al pannello] */
vite_d = 4.5;               // foro passante (M4)
testa_d = 7.6;              // testa a brugola M4 ISO 4762 = 7 mm
testa_h = 4.2;
mozzo_d = 13;
mozzo_l = 6;                // sporgenza del mozzo dalla schiena
spina = true;               // foro cieco per spina antirotazione nel pannello
spina_d = 6.2;
spina_prof = 7;
dima_pilota = 3.2;          // foro guida della dima per la vite

/* [Incastri tra cubi] */
lingua_sopra = true;        // linguetta sul lato alto (entra nel cubo sopra)
scanalatura_sotto = true;
lingua_dx = true;           // linguetta sul lato destro
scanalatura_sx = true;
lingua_w = 6;               // base della linguetta (fianchi a 45°)
lingua_h = 1.5;
lingua_gioco = 0.25;
magneti = true;             // sedi per magneti 6x3 sui fianchi che hanno un vicino
                            // (destra se lingua_dx, sinistra se scanalatura_sx)
magnete_d = 6.3;
magnete_h = 3.2;

/* [Nascosti] */
$fn = 48;
e = 0.01;

// ---------------------------------------------------------------------
// Dati dell'elemento
// ---------------------------------------------------------------------
dato = Z > 0 ? ELEMENTI[Z - 1] : ["", "", "", "", "", 0, 0];
function scegli(personale, tabella) = personale != "" ? personale : tabella;
T_NUMERO = scegli(numero_testo, Z > 0 ? str(dato[0]) : "");
T_SIMBOLO = scegli(simbolo_testo, dato[1]);
T_NOME = scegli(nome_testo, dato[2]);
T_MASSA = scegli(massa_testo, dato[3]);

// ---------------------------------------------------------------------
// Quote derivate
// ---------------------------------------------------------------------
z_appoggio = fascia_h - pav_sp;               // dove appoggia il pavimento
vite_x = parete + costola + mozzo_d / 2 - 0.5;
vite_z = fondo + (z_appoggio - fondo) / 2;
lingua_lato_z = vite_z + 2.7;                 // linguetta laterale, nel vano tecnico
magnete_lato_z = fondo + 2.5;
cavo_x = lato - parete - 3;
cavo_z = lato - cielo - 3.3;

// ---------------------------------------------------------------------
// Utilità
// ---------------------------------------------------------------------
// Prisma da un poligono nel piano Y-Z, esteso lungo X da x0 a x1
module prisma_yz(punti, x0, x1) {
    translate([x0, 0, 0]) rotate([90, 0, 90])
        linear_extrude(x1 - x0) polygon(punti);
}
// Prisma da un poligono nel piano X-Z, esteso lungo Y da y0 a y1
module prisma_xz(punti, y0, y1) {
    translate([0, y1, 0]) rotate([90, 0, 0])
        linear_extrude(y1 - y0) polygon(punti);
}
// Profilo trapezoidale della linguetta (base sul piano, punta verso +v)
function trapezio(w, h, g = 0) = [
    [-w / 2 - g, -e], [w / 2 + g, -e],
    [w / 2 - h + g, h + g], [-w / 2 + h - g, h + g]];

// ---------------------------------------------------------------------
// Corpo
// ---------------------------------------------------------------------
module guscio() {
    difference() {
        hull() {
            translate([smusso, 0, smusso]) cube([lato - 2 * smusso, e, lato - 2 * smusso]);
            translate([0, smusso, 0]) cube([lato, profondita - smusso, lato]);
        }
        translate([parete, -1, fondo])
            cube([lato - 2 * parete, profondita - schiena + 1, lato - fondo - cielo]);
    }
}

module cornice() {
    // fronte: bordo laterale + visiera + fascia
    difference() {
        intersection() {
            guscio_pieno();
            cube([lato, cornice_sp, lato]);
        }
        translate([cornice_lato, -1, fascia_h])
            cube([lato - 2 * cornice_lato, cornice_sp + 2, lato - fascia_h - visiera_h]);
        // smusso a 45° sul bordo dell'apertura
        hull() {
            translate([cornice_lato - smusso_apertura, -e, fascia_h - smusso_apertura])
                cube([lato - 2 * cornice_lato + 2 * smusso_apertura, e,
                      lato - fascia_h - visiera_h + 2 * smusso_apertura]);
            translate([cornice_lato, smusso_apertura, fascia_h])
                cube([lato - 2 * cornice_lato, e, lato - fascia_h - visiera_h]);
        }
    }
    // la visiera: cuneo a 45° che porta il LED
    prisma_yz([[0, lato - visiera_h], [cornice_sp, lato - visiera_h],
               [cornice_sp + visiera_h - cielo, lato - cielo + e], [0, lato - cielo + e]],
              parete - e, lato - parete + e);
    // dietro la fascia: lastra a 45° che regge il bordo anteriore del pavimento
    // (cava dietro, così si stampa senza supporti e senza sprecare materiale)
    y_b = cornice_sp + battuta;
    t = pav_sp * sqrt(2);
    prisma_yz([[y_b - t, z_appoggio], [y_b, z_appoggio],
               [y_b + z_appoggio - fondo, fondo - e], [y_b + z_appoggio - fondo - t, fondo - e]],
              parete - e, lato - parete + e);
}

module guscio_pieno() {
    hull() {
        translate([smusso, 0, smusso]) cube([lato - 2 * smusso, e, lato - 2 * smusso]);
        translate([0, smusso, 0]) cube([lato, profondita - smusso, lato]);
    }
}

module vano_tecnico() {
    y0 = cornice_sp;
    y1 = profondita - schiena + e;
    h = z_appoggio - fondo + e;
    // costole laterali su cui appoggia il pavimento
    for (x = [parete - e, lato - parete - costola + e])
        translate([x, y0, fondo - e]) cube([costola, y1 - y0, h]);
    // appoggio posteriore
    translate([parete, y1 - battuta, fondo - e]) cube([lato - 2 * parete, battuta, h]);
    // rinforzo sopra la scanalatura inferiore
    if (scanalatura_sotto)
        translate([lato / 2 - lingua_w / 2 - 2, y0, fondo - e]) cube([lingua_w + 4, y1 - y0, 1.6]);
    // mozzi: vite a sinistra, spina a destra
    for (x = [vite_x, lato - vite_x])
        hull() {
            translate([x, y1 - mozzo_l - battuta, vite_z]) rotate([-90, 0, 0])
                cylinder(d = mozzo_d, h = mozzo_l + battuta);
            translate([x - mozzo_d / 2, y1 - mozzo_l - battuta, fondo - e])
                cube([mozzo_d, mozzo_l + battuta, e]);
        }
}

module raccordi_alti() {
    for (s = [0, 1]) mirror([s, 0, 0]) translate([-s * lato, 0, 0])
        prisma_xz([[parete - e, lato - cielo + e], [parete + raccordo, lato - cielo + e],
                   [parete - e, lato - cielo - raccordo]],
                  cornice_sp, profondita - schiena + e);
}

module linguette() {
    if (lingua_sopra)
        translate([lato / 2, smusso, lato]) rotate([-90, 0, 0])
            linear_extrude(profondita - smusso)
                mirror([0, 1, 0]) polygon(trapezio(lingua_w, lingua_h));
    if (lingua_dx)
        translate([lato, smusso, lingua_lato_z]) rotate([-90, 0, 0])
            linear_extrude(profondita - smusso)
                rotate(90) mirror([0, 1, 0]) polygon(trapezio(lingua_w, lingua_h));
}

module scanalature() {
    if (scanalatura_sotto)
        translate([lato / 2, -1, 0]) rotate([-90, 0, 0])
            linear_extrude(profondita + 2)
                mirror([0, 1, 0]) polygon(trapezio(lingua_w, lingua_h, lingua_gioco));
    if (scanalatura_sx)
        translate([0, -1, lingua_lato_z]) rotate([-90, 0, 0])
            linear_extrude(profondita + 2)
                rotate(90) mirror([0, 1, 0]) polygon(trapezio(lingua_w, lingua_h, lingua_gioco));
}

module canale_led() {
    // centro del piano inclinato della visiera
    translate([0, cornice_sp + (visiera_h - cielo) / 2, lato - (visiera_h + cielo) / 2])
        rotate([45, 0, 0])
            translate([parete + 1, -led_larghezza / 2, -1])
                cube([lato - 2 * parete - 2, led_larghezza, led_profondita + 1]);
    // tunnel cavi dentro il raccordo alto destro, fino al retro
    translate([cavo_x, cornice_sp + 1, cavo_z]) rotate([-90, 0, 0])
        cylinder(d = cavo_d, h = profondita);
}

module fori_fissaggio() {
    y_mozzo = profondita - schiena - battuta - mozzo_l;
    // vite: passante + lamatura per la testa, accessibile dal vano tecnico
    translate([vite_x, y_mozzo - 1, vite_z]) rotate([-90, 0, 0]) {
        cylinder(d = vite_d, h = profondita);
        cylinder(d = testa_d, h = testa_h + 1);
    }
    // spina antirotazione: foro cieco dal retro
    if (spina)
        translate([lato - vite_x, profondita - spina_prof, vite_z]) rotate([-90, 0, 0])
            cylinder(d = spina_d, h = spina_prof + 1);
    // passacavi del vano tecnico
    if (foro_vano > 0)
        translate([lato / 2, profondita - schiena - battuta - 1, vite_z]) rotate([-90, 0, 0])
            cylinder(d = foro_vano, h = schiena + battuta + 2);
}

module sedi_magneti() {
    if (magneti) {
        for (y = [profondita * 0.3, profondita * 0.7]) {
            if (scanalatura_sx)
                translate([-1, y, magnete_lato_z]) rotate([0, 90, 0]) cylinder(d = magnete_d, h = magnete_h + 1);
            if (lingua_dx) translate([lato - magnete_h, y, magnete_lato_z]) rotate([0, 90, 0])
                cylinder(d = magnete_d, h = magnete_h + 1);
        }
    }
}

// ---------------------------------------------------------------------
// Testi (disegnati nel piano X-Z della fascia, verso -Y)
// ---------------------------------------------------------------------
// Larghezza media dei caratteri di Inter in rapporto a "size" (misurata):
// serve solo a ridurre i testi lunghi, OpenSCAD 2021 non sa misurarli.
function larghezza(t, dim, k) = len(t) * dim * k;
function adatta(t, dim, k, max_w) = len(t) == 0 ? dim : min(dim, max_w / (len(t) * k));

module testi_2d() {
    sx = cornice_lato + margine_testo;
    dx = lato - cornice_lato - margine_testo;
    utile = dx - sx;
    d_sim = adatta(T_SIMBOLO, dim_simbolo, 0.9, utile * 0.45);
    w_sim = larghezza(T_SIMBOLO, d_sim, 0.9);
    d_nome = adatta(T_NOME, dim_nome, 0.76, utile - w_sim - 6);
    // colonna sinistra: numero sopra, simbolo sotto (come nelle tavole classiche)
    translate([sx, 3.5 + d_sim + 2]) text(T_NUMERO, size = dim_numero, font = font_testo);
    translate([sx - 0.04 * d_sim, 3.5]) text(T_SIMBOLO, size = d_sim, font = font_simbolo);
    // colonna destra: nome e massa, allineati a destra, massa sulla linea del simbolo
    translate([dx, 3.5 + dim_massa + 4]) text(T_NOME, size = d_nome, font = font_simbolo, halign = "right");
    translate([dx, 3.5]) text(T_MASSA, size = dim_massa, font = font_testo, halign = "right");
}

module testi(h) {
    rotate([90, 0, 0]) linear_extrude(h) testi_2d();
}

module corpo() {
    difference() {
        union() {
            guscio();
            cornice();
            vano_tecnico();
            raccordi_alti();
            linguette();
            if (testo_modo == "rilievo") testi(testo_h);
        }
        scanalature();
        if (led) canale_led();
        fori_fissaggio();
        sedi_magneti();
        if (testo_modo == "inciso") translate([0, testo_h, 0]) testi(testo_h + 1);
    }
}

// ---------------------------------------------------------------------
// Pavimento estraibile (copre il vano tecnico, regge l'oggetto)
// ---------------------------------------------------------------------
module pavimento() {
    x0 = parete + gioco;
    y0 = cornice_sp + gioco;
    w = lato - 2 * parete - 2 * gioco;
    d = profondita - schiena - cornice_sp - 2 * gioco;
    difference() {
        translate([x0, y0, z_appoggio]) cube([w, d, pav_sp]);
        // tacca sul bordo posteriore: per sollevarlo e far passare i cavi
        translate([lato / 2, y0 + d, z_appoggio - 1]) cylinder(r = tacca_dito, h = pav_sp + 2);
    }
}

// ---------------------------------------------------------------------
// Dima per forare il pannello (si appoggia al pannello, vista frontale)
// ---------------------------------------------------------------------
module dima() {
    difference() {
        union() {
            cube([lato, lato, 2.4]);
            for (x = [vite_x, lato - vite_x]) translate([x, vite_z, 0]) cylinder(d = 14, h = 10);
        }
        translate([vite_x, vite_z, -1]) cylinder(d = dima_pilota, h = 20);
        if (spina) translate([lato - vite_x, vite_z, -1]) cylinder(d = spina_d - 0.2, h = 20);
        // segni per i fori passacavo (punta da 2 mm, poi si allarga)
        for (p = [[cavo_x, cavo_z], [lato / 2, vite_z]]) translate([p[0], p[1], -1]) cylinder(d = 2, h = 5);
        translate([lato / 2, lato / 2, 1.6]) linear_extrude(5)
            text("ALTO ↑", size = 8, font = font_simbolo, halign = "center");
    }
}

// ---------------------------------------------------------------------
// Uscita
// ---------------------------------------------------------------------
module per_stampa() {
    // retro sul piatto, fronte in alto
    translate([0, 0, profondita]) rotate([-90, 0, 0]) children();
}

if (parte == "corpo") per_stampa() corpo();
else if (parte == "pavimento") translate([0, 0, -z_appoggio]) pavimento();
else if (parte == "dima") dima();
else if (parte == "testo") per_stampa() testi(testo_h);
// stessi pezzi nella posizione "appesa", per anteprime e montaggi
else if (parte == "corpo_appeso") corpo();
else if (parte == "pavimento_appeso") pavimento();
else if (parte == "sezione") intersection() {
    union() { corpo(); pavimento(); }
    translate([lato / 2, -10, -10]) cube([lato, profondita + 20, lato + 20]);
}
else if (parte == "info")
    echo(VITE = [vite_x, vite_z], LATO = lato, CAVO_LED = [cavo_x, cavo_z], CAVO_VANO = [lato / 2, vite_z],
         PROFONDITA = profondita, CORNICE = cornice_sp);
else {
    color("#e9e6df") corpo();
    color("#b08d57") pavimento();
}
