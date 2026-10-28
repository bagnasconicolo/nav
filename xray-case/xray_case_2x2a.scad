// =====================================================================
//  Case schermato per tubo 2X2A usato come sorgente di raggi X
//  - doppia parete stampata con intercapedine per lastre di piombo 2 mm
//  - fondo e coperchio con lastra di piombo 2 mm
//  - finestra con membrana stampata (0,8 mm), filtro Al e otturatore piombato
//  - passacavi a labirinto (BT dal fondo, AT dal coperchio)
//
//  Uso:  openscad -D 'part="body"' -o body.stl xray_case_2x2a.scad
//  part = "assembly" | "section" | "body" | "lid" | "tray" | "hood" | "window_frame"
//         | "shutter" | "lead_long" | "lead_long_window" | "lead_short"
//         | "lead_floor" | "lead_lid" | "lead_shutter"
//         | "lead_hood_roof" | "lead_hood_side"
//  Le parti "lead_*" sono sagome 2D (esportare in .svg/.dxf) per tagliare
//  il piombo.  TUTTE le misure sono in mm.
// =====================================================================

part = "assembly";

// ---------- tubo 2X2A (MISURARE il proprio esemplare!) ----------
tube_d          = 38;   // diametro ampolla + margine (2X2A ~36 mm)
tube_seated_h   = 120;  // dal piano dello zoccolo alla cima del cappuccio anodico
anode_rim_h     = 55;   // dal piano dello zoccolo al BORDO INFERIORE della placca:
                        // e' li' che si concentra l'emissione (anello attorno al tubo)

// ---------- zoccolo UX4 e supporto ----------
socket_h        = 15;   // altezza zoccolo sopra il supporto
socket_hole     = 26;   // foro centrale per i piedini
socket_mount    = 42;   // interasse fori di fissaggio zoccolo
tray_h          = 20;   // altezza supporto (piedini + piastra)
tray_d          = 60;

// ---------- isolamento e schermatura ----------
hv_clear        = 40;   // distanza aria minima AT -> piombo (a massa); >= 1 mm/kV
lead_t          = 2.0;  // spessore piombo
lead_tol        = 0.4;  // gioco intercapedine
wall_in         = 2.4;  // parete interna stampata
wall_out        = 2.4;  // parete esterna stampata
floor_t         = 3;    // fondo stampato
chan_floor      = 1.2;  // spessore sotto l'intercapedine (piombo pareti scende sotto
                        // il piombo del fondo -> nessuna fessura in linea d'aria)
feet_h          = 5;

// ---------- finestra ----------
window_d        = 20;   // apertura nel piombo
membrane_t      = 0.8;  // membrana stampata (PETG 0,8 mm: ~3% di attenuazione a 30 keV)
filter_t        = 1.2;  // fessura filtro alluminio (0,5-1 mm Al)
boss_h          = 6;

// ---------- passacavi a labirinto ----------
hood_s          = 28;
hood_h          = 22;
cable_d         = 8;    // cavo AT siliconico 40 kV ~ 4-7 mm

$fn = 64;
eps = 0.01;

// ---------- grandezze derivate ----------
cav       = ceil(tube_d + 2*hv_clear);                    // lato cavita' interna
cav_h     = lead_t + tray_h + socket_h + tube_seated_h + hv_clear;
H         = floor_t + cav_h;                              // altezza corpo (senza piedini)
ch_t      = lead_t + lead_tol;
hi        = cav/2;                     // semilato cavita'
c_in      = hi + wall_in;              // semilato inizio intercapedine
c_out     = c_in + ch_t;               // semilato fine intercapedine
outer     = c_out + wall_out;          // semilato esterno
plate_h   = H - chan_floor;            // altezza lastre parete
win_z     = floor_t + lead_t + tray_h + socket_h + anode_rim_h; // quota centro finestra
hood_c    = hi - 8 - hood_s/2;         // centro passacavi (angolo)

lid_t     = 3;
skirt_h   = 12;
skirt_gap = 0.4;

echo(str("Cavita' ", cav, " x ", cav, " x ", cav_h, " mm"));
echo(str("Corpo esterno ", 2*outer, " x ", 2*outer, " x ", H + feet_h, " mm (stampa)"));
echo(str("Centro finestra a z = ", win_z, " mm dal fondo del corpo"));
echo(str("Lastre lunghe 2x: ", 2*c_out - lead_tol, " x ", plate_h));
echo(str("Lastre corte  2x: ", 2*c_in - lead_tol, " x ", plate_h));
echo(str("Fondo: ", cav - 0.5, " quadrata; coperchio: ", 2*outer, " quadrata"));
pb_area = 2*(2*c_out)*plate_h + 2*(2*c_in)*plate_h + pow(cav,2) + pow(2*outer,2);
echo(str("Piombo totale ~", round(pb_area*lead_t*11.35/1000), " g"));

// =====================================================================
module rsquare(s, r=3) { offset(r) offset(-r) square(s, center=true); }

// foro orizzontale a goccia (stampabile senza supporti), asse lungo Y
module teardrop_y(d, l) {
    rotate([90,0,0]) linear_extrude(l, center=true)
        union() { circle(d=d); rotate(45) square(d/2); }
}

// ------------------------- CORPO -------------------------
module body() {
    difference() {
        union() {
            translate([0,0,-feet_h]) linear_extrude(H + feet_h) rsquare(2*outer, 4);
            // borchie per la finestra (fori M3 autofilettanti, non passanti)
            for (p = win_holes()) translate([p[0], -outer, win_z + p[1]])
                rotate([90,0,0]) cylinder(d=9, h=boss_h);
        }
        // cavita'
        translate([0,0,floor_t]) linear_extrude(H) square(cav, center=true);
        // intercapedine per piombo (aperta in alto)
        translate([0,0,chan_floor]) linear_extrude(H)
            difference() { square(2*c_out, center=true); square(2*c_in, center=true); }
        // spazio sotto: piedini agli angoli, canale cavi al centro
        translate([0,0,-feet_h-eps]) linear_extrude(feet_h + eps)
            difference() {
                square(2*outer + 1, center=true);
                for (sx=[-1,1], sy=[-1,1]) translate([sx*(outer-10), sy*(outer-10)])
                    square(16, center=true);
            }
        // foro cavi BT nel fondo, sotto il passacavi
        translate([hood_c, -hood_c, -feet_h-1]) cylinder(d=cable_d, h=floor_t + feet_h + 2);
        // finestra: foro nella parete esterna
        translate([0, -(c_out + wall_out/2), win_z]) teardrop_y(window_d + 2, wall_out + 2);
        // finestra: membrana nella parete interna (assottigliata dal lato cavita')
        translate([0, -(hi + (wall_in - membrane_t)/2) + 0.5, win_z])
            teardrop_y(window_d + 2, wall_in - membrane_t + 1);
        // fori pilota M3
        for (p = win_holes()) translate([p[0], -outer + 1, win_z + p[1]])
            rotate([90,0,0]) cylinder(d=2.6, h=boss_h + 2);
    }
}

// posizioni fori finestra rispetto al centro apertura [x, z]
function win_holes() = [[-27,-20], [27,-20], [-27,45], [27,45]];

// ------------------------- COPERCHIO -------------------------
// stampare capovolto (piano superiore sul piatto). La lastra di piombo
// (quadrata 2*outer) si appoggia sui bordi del corpo e sulle lastre di parete,
// dentro la gonna, e si fissa con biadesivo.
module lid() {
    difference() {
        union() {
            translate([0,0,lead_t]) linear_extrude(lid_t) rsquare(2*outer + 2*(skirt_gap + 2.4), 6);
            translate([0,0,lead_t - skirt_h + lead_t]) linear_extrude(skirt_h)
                difference() {
                    rsquare(2*outer + 2*(skirt_gap + 2.4), 6);
                    square(2*outer + 2*skirt_gap, center=true);  // spigoli vivi: ci sta la lastra quadrata
                }
        }
        // foro cavo AT sopra il passacavi
        translate([hood_c, hood_c, -50]) cylinder(d=cable_d, h=100);
        // tacca per un microswitch di interblocco (opzionale)
        translate([-outer, 0, lead_t - skirt_h + lead_t - eps]) cube([12, 14, 8], center=true);
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
// esterne da 2,2 mm per il piombo. I due lati aperti guardano le pareti.
// Ogni raggio rettilineo dal tubo al foro deve attraversare tetto o fianchi.
// Stesso pezzo per fondo (incollato sul piombo del fondo) e coperchio
// (capovolto, incollato sotto la lastra del coperchio).
// Orientamento: lati aperti verso +X e +Y -> ruotare in fase di montaggio.
module hood() {
    w = 3.8;           // parete: 1,6 plastica + 2,2 tasca piombo
    difference() {
        cube([hood_s, hood_s, hood_h]);
        // vuoto interno, aperto su +X, +Y e sotto
        translate([w, w, -eps]) cube([hood_s, hood_s, hood_h - w + eps]);
        // tasca piombo tetto (dall'alto)
        translate([1, 1, hood_h - ch_t + eps]) cube([hood_s - 1 + eps, hood_s - 1 + eps, ch_t]);
        // tasche piombo fianchi (dall'esterno)
        translate([-eps, 1, -eps]) cube([ch_t, hood_s - 1 + eps, hood_h - ch_t + 2*eps]);
        translate([1, -eps, -eps]) cube([hood_s - 1 + eps, ch_t, hood_h - ch_t + 2*eps]);
    }
}

// ------------------------- FINESTRA -------------------------
fr_w   = 64;            // larghezza modulo
fr_bot = 27;            // distanza bordo inferiore -> centro apertura
fr_top = 55;            // distanza centro apertura -> bordo superiore
sh_w   = 44;  sh_t = 5.4;   // otturatore
pin_x  = 18;
fr_back = 3; fr_front = 2; fr_rib = 2;
fr_t   = fr_back + filter_t + fr_rib + sh_t + 0.6 + fr_front;

// Modulo da avvitare sulle borchie: (dal corpo verso l'esterno)
// piastra posteriore | fessura filtro Al | setto | canale otturatore | piastra frontale.
// Fessure aperte in alto. Stampare in piedi (come montato).
module window_frame() {
    difference() {
        translate([-fr_w/2, 0, -fr_bot]) cube([fr_w, fr_t, fr_bot + fr_top]);
        // apertura passante
        translate([0, fr_t/2, 0]) teardrop_y(window_d + 2, fr_t + 2);
        // fessura filtro (piastra Al 44 x 60)
        translate([-23, fr_back, -fr_bot + 2]) cube([46, filter_t, fr_bot + fr_top]);
        // canale otturatore
        translate([-(sh_w + 1)/2, fr_back + filter_t + fr_rib, -fr_bot + 2])
            cube([sh_w + 1, sh_t + 0.6, fr_bot + fr_top]);
        // fori M3 passanti
        for (p = win_holes()) translate([p[0], fr_t/2, p[1]]) rotate([90,0,0])
            cylinder(d=3.4, h=fr_t + 2, center=true);
        // foro perno "aperto" (d3), dal fronte attraverso il canale otturatore
        translate([pin_x, fr_back + filter_t + 0.6, fr_top - 8]) rotate([-90,0,0])
            cylinder(d=3.2, h=fr_t);
    }
}

// Otturatore: in basso tasca per piombo 30x30x2 (CHIUSO, posizione di riposo
// per gravita'); 40 mm piu' su un foro (APERTO, sollevato e bloccato col perno).
sh_len = 100;
module shutter() {
    difference() {
        translate([-sh_w/2, 0, 0]) cube([sh_w, sh_t, sh_len]);
        // tasca piombo (dal lato esterno, la plastica resta verso il tubo)
        translate([-15.2, 1.6, 25 - 15.2]) cube([30.4, sh_t, 30.4]);
        // foro "aperto"
        translate([0, sh_t/2, 65]) teardrop_y(window_d + 2, sh_t + 2);
        // foro perno per bloccarlo APERTO (fuori dalla tasca e dal foro)
        translate([pin_x, sh_t/2, fr_bot - 2 + fr_top - 8 - 40]) rotate([90,0,0])
            cylinder(d=3.2, h=sh_t + 2, center=true);
        // presa
        translate([0, sh_t/2, sh_len]) rotate([90,0,0]) cylinder(d=12, h=sh_t + 2, center=true);
    }
}

// ------------------------- SAGOME PIOMBO (2D) -------------------------
module lead_long(window=false) {
    L = 2*c_out - lead_tol;
    difference() {
        square([L, plate_h]);
        if (window) translate([L/2, win_z - chan_floor]) circle(d=window_d);
    }
}
module lead_short() square([2*c_in - lead_tol, plate_h]);
module lead_floor() {
    s = cav - 0.5;
    difference() {
        square(s, center=true);
        translate([hood_c, -hood_c]) circle(d=cable_d);
    }
}
module lead_lid() {
    difference() {
        square(2*outer, center=true);
        translate([hood_c, hood_c]) circle(d=cable_d);
    }
}

// ------------------------- ASSIEME -------------------------
module halfcut(cut) {
    if (cut) difference() { children(); translate([-300, 0, -100]) cube([600, 300, 600]); }
    else children();
}
module assembly(cut=false) {
    halfcut(cut) color("SteelBlue", cut ? 1 : 0.35) body();
    // piombo
    halfcut(cut) color("DimGray") {
        translate([0,0,floor_t]) linear_extrude(lead_t) square(cav - 0.5, center=true);
        for (s=[-1,1]) translate([-(2*c_out - lead_tol)/2, s*(c_in + lead_tol/2 + lead_t/2) - lead_t/2, chan_floor])
            cube([2*c_out - lead_tol, lead_t, plate_h]);
        for (s=[-1,1]) translate([s*(c_in + lead_tol/2 + lead_t/2) - lead_t/2, -(2*c_in - lead_tol)/2, chan_floor])
            cube([lead_t, 2*c_in - lead_tol, plate_h]);
    }
    color("Orange") translate([0,0,floor_t + lead_t]) tray();
    // tubo (indicativo)
    z0 = floor_t + lead_t + tray_h;
    color("Black") translate([0,0,z0]) cylinder(d=32, h=socket_h);
    color("LightCyan", cut ? 1 : 0.4) translate([0,0,z0 + socket_h]) cylinder(d=tube_d - 2, h=tube_seated_h - 8);
    color("Silver") translate([0,0,z0 + socket_h + anode_rim_h]) cylinder(d=16, h=30);
    color("Red") translate([0,0,z0 + socket_h + anode_rim_h]) cylinder(d=tube_d + 6, h=0.8);
    color("Silver") translate([0,0,z0 + socket_h + tube_seated_h - 8]) cylinder(d=9, h=8);
    // passacavi
    // lati aperti verso l'angolo (verso le pareti), tetto/fianchi piombati verso il tubo
    color("Orange") translate([hood_c - hood_s/2, -hood_c + hood_s/2, floor_t + lead_t])
        mirror([0,1,0]) hood();
    color("Orange") translate([hood_c - hood_s/2, hood_c - hood_s/2, H])
        mirror([0,0,1]) hood();
    // coperchio (sollevato)
    halfcut(cut) color("SteelBlue", 0.5) translate([0,0,H + 40]) lid();
    // finestra
    color("Orange") translate([0, -outer - boss_h, win_z]) mirror([0,1,0]) window_frame();
}

// ------------------------- SELETTORE -------------------------
if      (part == "assembly")          assembly();
else if (part == "section")           assembly(cut=true);
else if (part == "body")              body();
else if (part == "lid")               rotate([180,0,0]) lid();
else if (part == "tray")              rotate([180,0,0]) tray();
else if (part == "hood")              rotate([180,0,0]) hood();
else if (part == "window_frame")      window_frame();
else if (part == "shutter")           rotate([90,0,0]) shutter();
else if (part == "lead_long")         lead_long(false);
else if (part == "lead_long_window")  lead_long(true);
else if (part == "lead_short")        lead_short();
else if (part == "lead_floor")        lead_floor();
else if (part == "lead_lid")          lead_lid();
else if (part == "lead_shutter")      square(30);
else if (part == "lead_hood_roof")    square(hood_s - 1);
else if (part == "lead_hood_side")    square([hood_s - 1, hood_h - ch_t]);
