// =====================================================================
//  Case schermato per tubo 2X2A usato come sorgente di raggi X
//  Pensato per Creality K2 Pro (piano 300 x 300 x 300 mm).
//
//  - doppia parete stampata con intercapedine per N fogli di piombo da 1 mm
//    (default 3 -> 3 mm efficaci); i giunti d'angolo si alternano fra uno
//    strato e l'altro, cosi' nessuna fessura attraversa tutto lo spessore
//  - fondo e coperchio con N fogli da 1 mm
//  - finestra: membrana stampata 0,8 mm, fessura filtro Al, otturatore piombato
//  - passacavi a labirinto: BT dal fondo verso lo zoccolo, AT dal coperchio
//  - passante AT con alette (creepage) e serracavo
//  - zoccolo/basamento con pannello connettori (GX16, GX12, morsetto di terra)
//  - supporto microswitch di interblocco azionato dal coperchio
//
//  Uso:  openscad -D 'part="body"' -o body.stl xray_case_2x2a.scad
//        (oppure ./build.sh per rigenerare tutto)
//  part = "assembly" | "body" | "lid" | "plinth" | "tray" | "hood"
//         | "window_frame" | "shutter" | "hv_bushing"
//         | "lead_wall" (con layer=0..N-1, face="front"|"back"|"side")
//         | "lead_floor" | "lead_lid" | "lead_shutter" | "lead_hood_roof"
//         | "lead_hood_side"
//  Le parti "lead_*" sono sagome 2D 1:1 (esportare in .svg/.dxf).
//  TUTTE le misure sono in mm.
// =====================================================================

part  = "assembly";
layer = 0;          // solo per part="lead_wall"
face  = "front";    // solo per part="lead_wall"

// ---------- stampante ----------
printer = [300, 300, 300];   // Creality K2 Pro

// ---------- tubo 2X2A (MISURARE il proprio esemplare!) ----------
tube_d          = 38;   // diametro ampolla + margine (2X2A ~36 mm)
tube_seated_h   = 120;  // dal piano dello zoccolo alla cima del cappuccio anodico
anode_rim_h     = 55;   // dal piano dello zoccolo al BORDO INFERIORE della placca:
                        // e' li' che si concentra l'emissione (anello attorno al tubo)

// ---------- zoccolo UX4 e supporto ----------
socket_h        = 15;   // altezza zoccolo sopra il supporto
socket_hole     = 26;   // foro centrale per i piedini
socket_mount    = 42;   // interasse fori di fissaggio zoccolo
tray_h          = 20;
tray_d          = 64;

// ---------- schermatura ----------
lead_sheet      = 1.0;  // spessore di un foglio di piombo
lead_n          = 3;    // numero di fogli sovrapposti (2 -> 2 mm, 3 -> 3 mm)
lead_t          = lead_sheet * lead_n;
lead_tol        = 0.6;  // gioco intercapedine (fogli ondulati: abbondare)
hv_clear        = 50;   // distanza aria minima AT -> piombo (a massa); >= 1 mm/kV
wall_in         = 2.4;
wall_out        = 2.4;
floor_t         = 3;
chan_floor      = 1.2;  // l'intercapedine scende SOTTO il piombo del fondo

// ---------- finestra ----------
window_d        = 20;   // apertura nel piombo
membrane_t      = 0.8;  // PETG 0,8 mm: ~3% di attenuazione a 30 keV
filter_t        = 1.2;  // fessura filtro alluminio (0,5-1 mm Al)
boss_h          = 6;

// ---------- cavi ----------
hood_s          = 32;
hood_h          = 26;
cable_d         = 8;    // foro cavi (AT siliconico 40 kV: 4-7 mm)

// ---------- basamento e connettori ----------
plinth_h        = 50;
plinth_lip      = 4;    // bordo che centra il corpo
// [x, diametro, piatto (0 = tondo), etichetta]  sul lato posteriore (+Y)
connectors = [
    [-48, 16.2, 15.0, "FIL/K"],   // GX16-4: filamento (2) + catodo
    [-16, 12.2, 11.0, "INTLK"],   // GX12-2: interblocco
    [ 16,  8.0,  0,   "GND"],     // morsetto 4 mm / prigioniero: terra + piombo
    [ 48, 12.2, 11.0, "AUX"]      // GX12-3: riserva (sensore T, contatore...)
];
panel_t         = 3;    // spessore pannello in corrispondenza dei connettori

// ---------- interblocco (microswitch tipo KW11 20 x 6,4 x 10,2) ----------
sw_len = 20; sw_w = 6.4; sw_h = 10.2; sw_pitch = 9.5;

$fn = 64;
eps = 0.01;

// ---------- grandezze derivate ----------
cav       = ceil(tube_d + 2*hv_clear);
cav_h     = lead_t + tray_h + socket_h + tube_seated_h + hv_clear;
H         = floor_t + cav_h;
ch_t      = lead_t + lead_tol;
hi        = cav/2;
c_in      = hi + wall_in;
c_out     = c_in + ch_t;
outer     = c_out + wall_out;
plate_h   = H - chan_floor;
win_z     = floor_t + lead_t + tray_h + socket_h + anode_rim_h;
hood_c    = hi - 8 - hood_s/2;
lv_xy     = [ hood_c, hood_c];     // passacavi BT: angolo posteriore destro
hv_xy     = [-hood_c, hood_c];     // passante AT: angolo posteriore sinistro

lid_t     = 3;
skirt_h   = 14;
skirt_gap = 0.4;
skirt_w   = 2.4;
skirt_bot = H + lead_t - skirt_h + lead_t;   // quota bordo inferiore gonna
sw_top    = skirt_bot - 10;                  // quota bordo superiore microswitch
sw_x      = -8;                              // faccia di montaggio del microswitch

pl_out    = outer + skirt_gap + skirt_w + 0.5;   // semilato basamento (= ingombro coperchio)

echo(str("Cavita' ", cav, " x ", cav, " x ", cav_h, " mm"));
echo(str("Corpo ", 2*outer, " x ", 2*outer, " x ", H, " mm"));
echo(str("Basamento ", 2*pl_out, " x ", 2*pl_out, " x ", plinth_h + plinth_lip, " mm"));
echo(str("Piombo: ", lead_n, " fogli da ", lead_sheet, " mm = ", lead_t, " mm"));
echo(str("Centro finestra a z = ", win_z, " mm dal fondo del corpo"));
assert(H <= printer[2] && 2*pl_out <= printer[0], "Non entra nel piano di stampa!");
for (i = [0:lead_n-1]) echo(str("Strato ", i+1, ": fronte/retro ", wall_len(i, "front"),
    " x ", plate_h, ", lati (x2) ", wall_len(i, "side"), " x ", plate_h));
pb_area = lead_n*(4*(2*c_out)*plate_h + pow(cav,2) + pow(2*outer,2));
echo(str("Piombo totale ~", round(pb_area*lead_sheet*11.35/1000), " g"));

// =====================================================================
module rsquare(s, r=3) { offset(r) offset(-r) square(s, center=true); }

// foro orizzontale a goccia (stampabile senza supporti), asse lungo Y
module teardrop_y(d, l) {
    rotate([90,0,0]) linear_extrude(l, center=true)
        union() { circle(d=d); rotate(45) square(d/2); }
}
// foro "D" per connettori circolari con piatto antirotazione, asse lungo Y
module dhole_y(d, flat, l) {
    rotate([90,0,0]) linear_extrude(l, center=true)
        intersection() {
            circle(d=d);
            if (flat > 0) translate([0, flat/2 - d/2]) square([d, flat], center=true);
            else circle(d=d);
        }
}

// ------------------------- CORPO -------------------------
function win_holes() = [[-27,-20], [27,-20], [-27,45], [27,45]];

module body() {
    difference() {
        union() {
            linear_extrude(H) rsquare(2*outer, 4);
            // borchie per il modulo finestra (M3 autofilettanti, non passanti)
            for (p = win_holes()) translate([p[0], -outer, win_z + p[1]])
                rotate([90,0,0]) cylinder(d=9, h=boss_h);
            // blocco per il microswitch di interblocco (lato posteriore)
            translate([sw_x - 10, outer - eps, sw_top - sw_h - 6])
                cube([10, sw_len + 4, sw_h + 6]);
        }
        // cavita'
        translate([0,0,floor_t]) linear_extrude(H) square(cav, center=true);
        // intercapedine per il piombo (aperta in alto)
        translate([0,0,chan_floor]) linear_extrude(H)
            difference() { square(2*c_out, center=true); square(2*c_in, center=true); }
        // foro cavi BT nel fondo (sotto il passacavi, verso il basamento)
        translate([lv_xy[0], lv_xy[1], -1]) cylinder(d=cable_d, h=floor_t + 2);
        // finestra: foro nella parete esterna
        translate([0, -(c_out + wall_out/2), win_z]) teardrop_y(window_d + 2, wall_out + 2);
        // finestra: membrana nella parete interna (assottigliata dal lato cavita')
        translate([0, -(hi + (wall_in - membrane_t)/2) + 0.5, win_z])
            teardrop_y(window_d + 2, wall_in - membrane_t + 1);
        // fori pilota M3
        for (p = win_holes()) translate([p[0], -outer + 1, win_z + p[1]])
            rotate([90,0,0]) cylinder(d=2.6, h=boss_h + 2);
        // fori M2 microswitch
        for (k = [0,1]) translate([sw_x - 6, outer + 2 + (sw_len - sw_pitch)/2 + k*sw_pitch,
                                   sw_top - sw_h + 2.9])
            rotate([0,90,0]) cylinder(d=1.8, h=10);
    }
}

// ------------------------- COPERCHIO -------------------------
// Stampare capovolto. I fogli di piombo (quadrati 2*outer) si appoggiano sui
// bordi del corpo e sulle lastre di parete, dentro la gonna (biadesivo).
module lid() {
    z0 = H + lead_t;                  // faccia inferiore del piano del coperchio
    difference() {
        union() {
            translate([0,0,z0]) linear_extrude(lid_t) rsquare(2*pl_out, 6);
            translate([0,0,skirt_bot]) linear_extrude(z0 - skirt_bot + eps)
                difference() {
                    rsquare(2*pl_out, 6);
                    square(2*outer + 2*skirt_gap, center=true);
                }
            // dito che preme il microswitch a coperchio chiuso
            translate([sw_x, outer + skirt_gap, sw_top + 2])
                cube([sw_w, sw_len, skirt_bot - sw_top]);
        }
        // foro passante AT
        translate([hv_xy[0], hv_xy[1], z0 - 1]) cylinder(d=cable_d, h=lid_t + 2);
        for (a=[0,120,240]) translate([hv_xy[0], hv_xy[1], z0 - 1])
            rotate(a) translate([15,0,0]) cylinder(d=2.6, h=lid_t + 2);
    }
}

// ------------------------- PASSANTE AT -------------------------
// Tubo con alette (allunga il percorso superficiale) + serracavo a vite in cima.
// Va sul coperchio sopra il foro AT, fissato con 3 viti M3.
module hv_bushing() {
    L = 60;
    difference() {
        union() {
            cylinder(d=40, h=4);
            cylinder(d=16, h=L);
            for (z=[8:12:L-18]) translate([0,0,z]) cylinder(d1=16, d2=30, h=7);   // alette a 45 gradi
            // orecchie del serracavo
            translate([0,0,L-12]) linear_extrude(12) square([34, 10], center=true);
        }
        translate([0,0,-1]) cylinder(d=cable_d - 1.5, h=L + 2);   // il cavo entra un po' stretto
        for (a=[0,120,240]) rotate(a) translate([15,0,-1]) cylinder(d=3.4, h=6);
        // fessura serracavo + vite M3 trasversale
        translate([0,0,L-14]) linear_extrude(15) square([40, 1.6], center=true);
        for (s=[-1,1]) translate([s*12.5, 0, L-6]) rotate([90,0,0]) cylinder(d=3.4, h=12, center=true);
    }
}

// ------------------------- BASAMENTO CON CONNETTORI -------------------------
// Vaschetta aperta in alto: il corpo ci si appoggia sopra e la chiude.
// I cavi BT scendono dal foro del fondo, l'interblocco entra dalla tacca posteriore.
// Stampare cosi' com'e' (fondo sul piatto, nessun supporto).
module plinth() {
    pf = 3;
    difference() {
        linear_extrude(plinth_h + plinth_lip) rsquare(2*pl_out, 6);
        // interno
        translate([0,0,pf]) linear_extrude(plinth_h + plinth_lip) rsquare(2*(outer - 5), 3);
        // sede del corpo (gradino)
        translate([0,0,plinth_h]) linear_extrude(plinth_lip + 1) rsquare(2*outer + 1, 4.5);
        // connettori sul lato posteriore + assottigliamento parete dall'interno
        for (c = connectors) {
            translate([c[0], pl_out - 2, pf + (plinth_h - pf)/2]) dhole_y(c[1], c[2], 10);
            translate([c[0] - 13, 0, pf]) cube([26, pl_out - panel_t, plinth_h - pf - 6]);
            translate([c[0], pl_out - 0.6, pf + (plinth_h - pf)/2 + c[1]/2 + 4])
                rotate([90,0,180]) linear_extrude(1) text(c[3], size=5, halign="center",
                                                          font="Liberation Sans:style=Bold");
        }
        // tacca per i fili dell'interblocco
        translate([sw_x - 2, outer - 1, plinth_h - 6]) cube([10, 10, 20]);
        // feritoie di ventilazione laterali (zona BT, fuori dallo schermo)
        for (s=[-1,1], k=[-2:2]) translate([s*pl_out, k*14, plinth_h/2])
            cube([22, 5, 22], center=true);
    }
}

// ------------------------- SUPPORTO ZOCCOLO -------------------------
module tray() {
    difference() {
        union() {
            translate([0,0,tray_h-4]) cylinder(d=tray_d, h=4);
            for (a=[90, 210, 330]) rotate(a) translate([tray_d/2 - 6, 0, 0])
                cylinder(d=10, h=tray_h);
        }
        translate([0,0,-1]) cylinder(d=socket_hole, h=tray_h + 2);
        for (sx=[-1,1]) translate([sx*socket_mount/2, 0, -1]) cylinder(d=3.4, h=tray_h + 2);
    }
}

// ------------------------- PASSACAVI A LABIRINTO -------------------------
// Copertura a "L": tetto + due fianchi rivolti verso il tubo, con tasche
// esterne per lead_n fogli. I due lati aperti guardano le pareti.
// Ogni raggio rettilineo dal tubo al foro deve attraversare tetto o fianchi.
// Stesso pezzo per fondo e coperchio (capovolto). Lati aperti: +X e +Y.
hood_pk = lead_t + 0.4;
module hood() {
    w = 1.6 + hood_pk;
    difference() {
        cube([hood_s, hood_s, hood_h]);
        translate([w, w, -eps]) cube([hood_s, hood_s, hood_h - w + eps]);
        translate([1, 1, hood_h - hood_pk + eps]) cube([hood_s - 1 + eps, hood_s - 1 + eps, hood_pk]);
        translate([-eps, 1, -eps]) cube([hood_pk, hood_s - 1 + eps, hood_h - hood_pk + 2*eps]);
        translate([1, -eps, -eps]) cube([hood_s - 1 + eps, hood_pk, hood_h - hood_pk + 2*eps]);
    }
}

// ------------------------- FINESTRA -------------------------
fr_w   = 64;
fr_bot = 27;
fr_top = 55;
sh_w   = 44;  sh_t = 1.6 + lead_t + 0.6;
pin_x  = 18;
fr_back = 3; fr_front = 2; fr_rib = 2;
fr_t   = fr_back + filter_t + fr_rib + sh_t + 0.6 + fr_front;

// Dal corpo verso l'esterno: piastra posteriore | fessura filtro Al | setto |
// canale otturatore | piastra frontale. Fessure aperte in alto. Stampare in piedi.
module window_frame() {
    difference() {
        translate([-fr_w/2, 0, -fr_bot]) cube([fr_w, fr_t, fr_bot + fr_top]);
        translate([0, fr_t/2, 0]) teardrop_y(window_d + 2, fr_t + 2);
        translate([-23, fr_back, -fr_bot + 2]) cube([46, filter_t, fr_bot + fr_top]);
        translate([-(sh_w + 1)/2, fr_back + filter_t + fr_rib, -fr_bot + 2])
            cube([sh_w + 1, sh_t + 0.6, fr_bot + fr_top]);
        for (p = win_holes()) translate([p[0], fr_t/2, p[1]]) rotate([90,0,0])
            cylinder(d=3.4, h=fr_t + 2, center=true);
        translate([pin_x, fr_back + filter_t + 0.6, fr_top - 8]) rotate([-90,0,0])
            cylinder(d=3.2, h=fr_t);
    }
}

// Otturatore: in basso tasca per lead_n fogli 30x30 (CHIUSO, riposo per gravita');
// 40 mm piu' su un foro (APERTO, sollevato e bloccato col perno).
sh_len = 100;
module shutter() {
    difference() {
        translate([-sh_w/2, 0, 0]) cube([sh_w, sh_t, sh_len]);
        translate([-15.2, 1.6, 25 - 15.2]) cube([30.4, sh_t, 30.4]);
        translate([0, sh_t/2, 65]) teardrop_y(window_d + 2, sh_t + 2);
        translate([pin_x, sh_t/2, fr_bot - 2 + fr_top - 8 - 40]) rotate([90,0,0])
            cylinder(d=3.2, h=sh_t + 2, center=true);
        translate([0, sh_t/2, sh_len]) rotate([90,0,0]) cylinder(d=12, h=sh_t + 2, center=true);
    }
}

// ------------------------- SAGOME PIOMBO (2D) -------------------------
// Strato i (0 = il piu' interno). Negli strati pari le lastre lunghe sono
// davanti/dietro, nei dispari ai lati: i giunti d'angolo risultano sfalsati.
function r_layer(i) = c_in + lead_tol/2 + i*lead_sheet;
function y_long(i) = (i % 2 == 0);
function wall_len(i, f) =
    let(long = (f == "side") ? !y_long(i) : y_long(i))
    long ? 2*(r_layer(i) + lead_sheet) - 0.3 : 2*r_layer(i) - 0.3;

module lead_wall(i, f) {
    L = wall_len(i, f);
    difference() {
        square([L, plate_h]);
        if (f == "front") translate([L/2, win_z - chan_floor]) circle(d=window_d);
    }
}
module lead_floor() {
    difference() {
        square(cav - 0.5, center=true);
        translate(lv_xy) circle(d=cable_d);
    }
}
module lead_lid() {
    difference() {
        square(2*outer, center=true);
        translate(hv_xy) circle(d=cable_d);
    }
}

// ------------------------- ASSIEME -------------------------
module halfcut(cut) {
    if (cut) difference() { children(); translate([-300, 0, -100]) cube([600, 300, 600]); }
    else children();
}
module assembly(cut=false) {
    translate([0,0,-plinth_h]) color("DarkSlateGray") plinth();
    halfcut(cut) color("SteelBlue", cut ? 1 : 0.35) body();
    // piombo (fogli da 1 mm, colori alternati per vedere i giunti sfalsati)
    halfcut(cut) for (i = [0:lead_n-1]) color(i % 2 ? "Gray" : "DimGray") {
        translate([0,0,floor_t + i*lead_sheet]) linear_extrude(lead_sheet) square(cav - 0.5, center=true);
        r = r_layer(i);
        for (s=[-1,1]) {
            Ly = wall_len(i, "front");  Lx = wall_len(i, "side");
            translate([-Ly/2, s*(r + lead_sheet/2) - lead_sheet/2, chan_floor]) cube([Ly, lead_sheet, plate_h]);
            translate([s*(r + lead_sheet/2) - lead_sheet/2, -Lx/2, chan_floor]) cube([lead_sheet, Lx, plate_h]);
        }
    }
    color("Orange") translate([0,0,floor_t + lead_t]) tray();
    z0 = floor_t + lead_t + tray_h;
    color("Black") translate([0,0,z0]) cylinder(d=32, h=socket_h);
    color("LightCyan", cut ? 1 : 0.4) translate([0,0,z0 + socket_h]) cylinder(d=tube_d - 2, h=tube_seated_h - 8);
    color("Silver") translate([0,0,z0 + socket_h + anode_rim_h]) cylinder(d=16, h=30);
    color("Red") translate([0,0,z0 + socket_h + anode_rim_h]) cylinder(d=tube_d + 6, h=0.8);
    color("Silver") translate([0,0,z0 + socket_h + tube_seated_h - 8]) cylinder(d=9, h=8);
    // passacavi: lati aperti verso l'angolo, tetto/fianchi piombati verso il tubo
    color("Orange") translate([lv_xy[0] - hood_s/2, lv_xy[1] - hood_s/2, floor_t + lead_t]) hood();
    color("Orange") translate([hv_xy[0] + hood_s/2, hv_xy[1] - hood_s/2, H])
        mirror([1,0,0]) mirror([0,0,1]) hood();
    // microswitch (indicativo)
    color("Black") translate([sw_x, outer + 2, sw_top - sw_h]) cube([sw_w, sw_len, sw_h]);
    // coperchio + passante AT (sollevati)
    translate([0,0,60]) {
        halfcut(cut) color("SteelBlue", 0.5) lid();
        color("Orange") translate([hv_xy[0], hv_xy[1], H + lead_t + lid_t]) hv_bushing();
    }
    color("Orange") translate([0, -outer - boss_h, win_z]) mirror([0,1,0]) window_frame();
}

// ------------------------- SELETTORE -------------------------
if      (part == "assembly")          assembly();
else if (part == "section")           assembly(cut=true);
else if (part == "body")              body();
else if (part == "lid")               rotate([180,0,0]) lid();
else if (part == "plinth")            plinth();
else if (part == "hv_bushing")        hv_bushing();
else if (part == "tray")              rotate([180,0,0]) tray();
else if (part == "hood")              rotate([180,0,0]) hood();
else if (part == "window_frame")      window_frame();
else if (part == "shutter")           rotate([90,0,0]) shutter();
else if (part == "lead_wall")         lead_wall(layer, face);
else if (part == "lead_floor")        lead_floor();
else if (part == "lead_lid")          lead_lid();
else if (part == "lead_shutter")      square(30);
else if (part == "lead_hood_roof")    square(hood_s - 1);
else if (part == "lead_hood_side")    square([hood_s - 1, hood_h - hood_pk]);
