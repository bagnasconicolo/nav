// =====================================================================
//  Tavola periodica a cubi espositivi - cubo parametrico
// ---------------------------------------------------------------------
//  Uso normale: cambiare solo Z (numero atomico) ed esportare.
//  Per testi personalizzati: Z = 0 e compilare i campi *_testo.
//  Esportazione in blocco: python3 strumenti/tavola.py esporta
//
//  Sistema di riferimento (cubo "appeso"): X verso destra, Y dal fronte
//  (y = 0, aperto) verso il retro, Z verso l'alto. L'esportazione ruota
//  il pezzo "sdraiato": retro sul piatto, fronte con la scritta in alto.
//  In quella posizione non servono supporti.
// =====================================================================

include <elementi.scad>

/* [Elemento] */
Z = 26;                     // numero atomico (0 = testi personalizzati)
numero_testo = "";          // se non vuoti, sostituiscono i dati della tabella
simbolo_testo = "";
nome_testo = "";
mostra_numero = true;

/* [Parte da generare] */
parte = "assemblato";       // [assemblato, corpo, testo, pavimento, dima, corpo_appeso, pavimento_appeso, sezione, info]

/* [Dimensioni] */
lato = 100;                 // larghezza = altezza
profondita = 100;
parete = 1.6;               // pareti laterali (4 linee da 0,4)
fondo = 2;                  // parete inferiore
cielo = 2;                  // parete superiore
schiena = 1.6;              // parete posteriore (sta sul piatto)
smusso = 0.6;               // smusso sugli spigoli anteriori

/* [Cornice e targhetta] */
cornice_sp = 3;             // spessore della cornice frontale
visiera_h = 10;             // fascia alta: nasconde il LED
fascia_h = 13;              // fascia bassa con i testi (= quota del piano espositivo)
smusso_apertura = 1;        // smusso a 45° sul bordo dell'apertura
testo_modo = "rilievo";     // [rilievo, inciso]
testo_h = 0.6;              // altezza del rilievo / profondità dell'incisione
font_simbolo = "Inter:style=Bold";
font_testo = "Inter:style=SemiBold";
// dimensioni massime: il nome si riduce da solo se è lungo
dim_simbolo = 7.5;
dim_numero = 3.4;
dim_nome = 4.6;
margine_testo = 3.5;

/* [Illuminazione] */
led = true;                 // canale per striscia LED sotto la visiera, inclinato a 45°
led_larghezza = 5.5;        // striscia COB da 5 mm
led_profondita = 1.6;
cavo_d = 3.5;               // tunnel cavi nello spigolo alto destro, esce dal retro
raccordo = 9;               // smusso interno negli spigoli alti (contiene il tunnel)
foro_vano = 7;              // foro passacavi del vano tecnico (0 = niente)

/* [Vano tecnico e pavimento] */
costola = 2;                // appoggi laterali del pavimento
battuta = 2.5;              // appoggio anteriore del pavimento
blocco_retro = 5;           // appoggio posteriore, contiene vite e spina
pav_sp = 2;                 // spessore del pavimento estraibile
gioco = 0.3;
tacca_dito = 8;             // raggio della tacca per sollevare il pavimento

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
$fn = 48;
e = 0.01;

// ---------------------------------------------------------------------
// Dati dell'elemento
// ---------------------------------------------------------------------
dato = Z > 0 ? ELEMENTI[Z - 1] : ["", "", "", "", "", 0, 0];
function scegli(personale, tabella) = personale != "" ? personale : tabella;
T_NUMERO = mostra_numero ? scegli(numero_testo, Z > 0 ? str(dato[0]) : "") : "";
T_SIMBOLO = scegli(simbolo_testo, dato[1]);
T_NOME = scegli(nome_testo, dato[2]);

// ---------------------------------------------------------------------
// Quote derivate
// ---------------------------------------------------------------------
z_appoggio = fascia_h - pav_sp;               // dove appoggia il pavimento
y_blocco = profondita - schiena - blocco_retro;
vite_x = parete + costola + svasatura_d / 2 + 1;
vite_z = fondo + (z_appoggio - fondo) / 2;
lingua_lato_z = vite_z;                       // linguetta laterale, nel vano tecnico
cavo_x = lato - parete - 2.6;
cavo_z = lato - cielo - 2.6;
y_led = cornice_sp + (visiera_h - cielo) / 2; // centro del piano inclinato del LED
z_led = lato - (visiera_h + cielo) / 2;

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
module guscio_pieno() {
    hull() {
        translate([smusso, 0, smusso]) cube([lato - 2 * smusso, e, lato - 2 * smusso]);
        translate([0, smusso, 0]) cube([lato, profondita - smusso, lato]);
    }
}

module guscio() {
    difference() {
        guscio_pieno();
        translate([parete, -1, fondo])
            cube([lato - 2 * parete, profondita - schiena + 1, lato - fondo - cielo]);
    }
}

module cornice() {
    // fronte: solo visiera e fascia, ai lati l'apertura arriva alle pareti
    difference() {
        intersection() {
            guscio_pieno();
            cube([lato, cornice_sp, lato]);
        }
        translate([parete, -1, fascia_h])
            cube([lato - 2 * parete, cornice_sp + 2, lato - fascia_h - visiera_h]);
        // smusso a 45° sul bordo dell'apertura
        hull() {
            translate([parete - smusso_apertura, -e, fascia_h - smusso_apertura])
                cube([lato - 2 * parete + 2 * smusso_apertura, e,
                      lato - fascia_h - visiera_h + 2 * smusso_apertura]);
            translate([parete, smusso_apertura, fascia_h])
                cube([lato - 2 * parete, e, lato - fascia_h - visiera_h]);
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

module vano_tecnico() {
    y0 = cornice_sp;
    y1 = profondita - schiena + e;
    h = z_appoggio - fondo + e;
    // costole laterali su cui appoggia il pavimento (ospitano la scanalatura sinistra)
    for (x = [parete - e, lato - parete - costola + e])
        translate([x, y0, fondo - e]) cube([costola, y1 - y0, h]);
    // blocco posteriore: appoggio del pavimento, vite e spina
    translate([parete, y_blocco, fondo - e]) cube([lato - 2 * parete, blocco_retro + e, h]);
    // rinforzo sopra la scanalatura inferiore
    if (scanalatura_sotto)
        translate([lato / 2 - lingua_w / 2 - 2, y0, fondo - e]) cube([lingua_w + 4, y1 - y0, 1.6]);
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
    translate([0, y_led, z_led]) rotate([45, 0, 0])
        translate([parete + 1, -led_larghezza / 2, -1])
            cube([lato - 2 * parete - 2, led_larghezza, led_profondita + 1]);
    // tunnel cavi dentro il raccordo alto destro, fino al retro
    translate([cavo_x, cornice_sp + 1, cavo_z]) rotate([-90, 0, 0])
        cylinder(d = cavo_d, h = profondita);
}

module fori_fissaggio() {
    // vite a testa svasata: la testa resta a filo del blocco, sotto il pavimento.
    // Il cono si allarga verso il fronte, cioè verso l'alto in stampa: niente supporti.
    translate([vite_x, 0, vite_z]) rotate([-90, 0, 0]) {
        translate([0, 0, y_blocco - 1]) cylinder(d = vite_d, h = profondita);
        translate([0, 0, y_blocco - 1]) cylinder(d = svasatura_d, h = 1 + e);
        translate([0, 0, y_blocco]) cylinder(d1 = svasatura_d, d2 = vite_d, h = (svasatura_d - vite_d) / 2);
    }
    // spina antirotazione: foro cieco dal retro
    if (spina)
        translate([lato - vite_x, profondita - spina_prof, vite_z]) rotate([-90, 0, 0])
            cylinder(d = spina_d, h = spina_prof + 1);
    // passacavi del vano tecnico
    if (foro_vano > 0)
        translate([lato / 2, y_blocco - 1, vite_z]) rotate([-90, 0, 0])
            cylinder(d = foro_vano, h = blocco_retro + schiena + 2);
}

// ---------------------------------------------------------------------
// Testi: una riga sola. Numero piccolo e simbolo a sinistra, nome a destra.
// ---------------------------------------------------------------------
// Larghezza media dei caratteri di Inter in rapporto a "size" (misurata):
// serve a impaginare e ridurre i testi lunghi, OpenSCAD 2021 non sa misurarli.
function larghezza(t, dim, k) = len(t) * dim * k;
function adatta(t, dim, k, max_w) = len(t) == 0 ? dim : min(dim, max_w / (len(t) * k));

module testi_2d() {
    sx = parete + margine_testo;
    dx = lato - parete - margine_testo;
    base = (fascia_h - smusso_apertura - dim_simbolo) / 2;   // simbolo centrato nella fascia
    w_num = len(T_NUMERO) > 0 ? larghezza(T_NUMERO, dim_numero, 0.66) + 1.6 : 0;
    w_sim = larghezza(T_SIMBOLO, dim_simbolo, 0.9);
    d_nome = adatta(T_NOME, dim_nome, 0.76, dx - sx - w_num - w_sim - 6);
    // numero in alto, allineato alla cima del simbolo (come un esponente)
    translate([sx, base + dim_simbolo - dim_numero])
        text(T_NUMERO, size = dim_numero, font = font_testo);
    translate([sx + w_num, base]) text(T_SIMBOLO, size = dim_simbolo, font = font_simbolo);
    translate([dx, base]) text(T_NOME, size = d_nome, font = font_testo, halign = "right");
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
            // telaio leggero invece di una lastra piena
            difference() {
                cube([lato, lato, 2]);
                translate([22, 22, -1]) cube([lato - 44, lato - 44, 4]);
            }
            for (x = [vite_x, lato - vite_x]) translate([x, vite_z, 0]) cylinder(d = 12, h = 10);
            translate([lato / 2 - 8, vite_z - 6, 0]) cube([16, 12, 2]);
        }
        translate([vite_x, vite_z, -1]) cylinder(d = dima_pilota, h = 20);
        if (spina) translate([lato - vite_x, vite_z, -1]) cylinder(d = spina_d - 0.2, h = 20);
        // segni per i fori passacavo (punta da 2 mm, poi si allarga)
        for (p = [[cavo_x, cavo_z], [lato / 2, vite_z]]) translate([p[0], p[1], -1]) cylinder(d = 2, h = 5);
        translate([lato / 2, lato - 14, 1.2]) linear_extrude(5)
            text("ALTO", size = 6, font = font_simbolo, halign = "center");
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
else if (parte == "pavimento") translate([0, 0, -z_appoggio]) pavimento();
else if (parte == "dima") dima();
// solo i testi, già nella posizione di stampa: per assegnare loro un altro filamento
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
    color("#3b3d40") pavimento();
}
