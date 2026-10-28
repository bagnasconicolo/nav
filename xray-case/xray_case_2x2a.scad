// =====================================================================
//  Case schermato CILINDRICO per tubo 2X2A usato come sorgente di raggi X
//  Pensato per Creality K2 Pro (piano 300 x 300 x 300 mm).
//
//  Costruzione "a tubo":
//   - CUP: bicchiere interno stampato (isolante, parete 3 mm) con fondo e flangia
//   - il piombo (N fogli da 1 mm, default 3) si AVVOLGE attorno al bicchiere,
//     giunti sfalsati fra gli strati, poi si infila sopra il MANICOTTO esterno
//   - fondo e coperchio: N dischi da 1 mm
//   - camini a labirinto piombati fuori asse per cavo AT (coperchio) e cavi BT (fondo):
//     nessuna linea retta dal tubo esce dai fori (verifica automatica qui sotto)
//   - finestra: membrana stampata 0,8 mm, fessura filtro Al, otturatore piombato
//   - basamento con pannello connettori (GX16, GX12 x2, terra), interblocco sul coperchio
//
//  Uso:  openscad -D 'part="cup"' -o cup.stl xray_case_2x2a.scad   (oppure ./build.sh)
//  part = "assembly" | "cup" | "sleeve" | "lid" | "plinth" | "tray" | "lv_chimney"
//         | "hv_bushing" | "window_frame" | "shutter"
//         | "lead_wall" (con layer=0..N-1) | "lead_floor" | "lead_lid"
//         | "lead_chimney_hv" | "lead_chimney_lv" | "lead_shutter"
//  Le parti "lead_*" sono sagome 2D 1:1 (esportare in .svg/.dxf). Misure in mm.
// =====================================================================

part  = "assembly";
layer = 0;          // solo per part="lead_wall"

printer = [300, 300, 300];   // Creality K2 Pro

// ---------- tubo 2X2A (MISURARE il proprio esemplare!) ----------
tube_d          = 38;   // diametro ampolla + margine (2X2A ~36 mm)
tube_seated_h   = 120;  // dal piano dello zoccolo alla cima del cappuccio anodico
anode_rim_h     = 55;   // dal piano dello zoccolo al BORDO INFERIORE della placca
anode_r         = 9;    // raggio della placca (per la verifica dei camini)

// ---------- zoccolo UX4 e supporto ----------
socket_h        = 15;
socket_hole     = 26;
socket_mount    = 42;
tray_h          = 14;   // spazio sotto lo zoccolo per piedini e saldature
tray_d          = 56;

// ---------- schermatura e isolamento ----------
lead_sheet      = 1.0;  // spessore di un foglio
lead_n          = 3;    // fogli sovrapposti (2 -> 2 mm, 3 -> 3 mm)
lead_t          = lead_sheet * lead_n;
lead_tol        = 1.0;  // gioco radiale totale per i fogli avvolti
hv_clear        = 35;   // aria fra VETRO del tubo e parete (la placca e' ~10 mm piu' dentro)
top_clear       = 40;   // aria fra cappuccio anodico e piombo del coperchio
wall_in         = 3.0;  // parete del bicchiere: e' anche isolante -> stampare al 100%
wall_out        = 2.0;  // manicotto esterno
floor_t         = 4;
fl_t            = 2;    // flangia alla base del bicchiere (il piombo di parete parte da qui,
                        // SOTTO il piombo del fondo)

// ---------- finestra ----------
window_d        = 20;
membrane_t      = 0.8;
filter_t        = 1.2;
boss_h          = 6;

// ---------- camini a labirinto (cavi) ----------
cable_d         = 8;    // foro (AT siliconico 40 kV: 4-7 mm; BT: 3 fili)
hv_off          = 40;   // distanza dall'asse del foro AT (coperchio)
lv_off          = 40;   // distanza dall'asse del foro BT (fondo)
hv_ch_L         = 50;   // lunghezza piombo del camino AT
lv_ch_L         = 40;   // lunghezza piombo del camino BT

// ---------- basamento e connettori ----------
plinth_h        = 58;
plinth_lip      = 4;
// [x, z, diametro, piatto (0 = tondo), etichetta]  sul retro piatto (+Y)
connectors = [
    [-13, 42, 16.2, 15.0, "FIL/K"],   // GX16-4: filamento (2) + catodo
    [ 13, 42, 12.2, 11.0, "INTLK"],   // GX12-2: interblocco
    [-13, 18,  8.0,  0,   "GND"],     // morsetto 4 mm / prigioniero: terra + piombo
    [ 13, 18, 12.2, 11.0, "AUX"]      // GX12-3: riserva
];
panel_t         = 3;
pl_flat_w       = 54;   // larghezza del retro piatto

// ---------- interblocco (microswitch tipo KW11 20 x 6,4 x 10,2) ----------
sw_len = 20; sw_w = 6.4; sw_h = 10.2; sw_pitch = 9.5;
sw_x   = -8;

$fn = 96;
eps = 0.01;

// ---------- grandezze derivate ----------
cav_r     = tube_d/2 + hv_clear;
cup_or    = cav_r + wall_in;
sl_ir     = cup_or + lead_t + lead_tol;
sl_or     = sl_ir + wall_out;
cav_h     = lead_t + tray_h + socket_h + tube_seated_h + top_clear;
H         = floor_t + cav_h;
plate_h   = H - fl_t;
win_z     = floor_t + lead_t + tray_h + socket_h + anode_rim_h;
hv_xy     = [-hv_off*cos(45), hv_off*sin(45)];     // posteriore sinistra
lv_xy     = [ lv_off*cos(45), -lv_off*sin(45)];    // anteriore destra
seam_off  = [0, 40, -40, 80, -80, 120];            // sfalsamento giunti (gradi)
win_ang   = 270;                                   // finestra verso -Y

lid_t     = 3;
skirt_h   = 14;
skirt_gap = 0.4;
skirt_w   = 2.4;
skirt_bot = H - 8;
sw_top    = skirt_bot - 10;
key_x     = 8;

R_pl      = sl_or + 3.5;
pl_flat_y = sqrt(R_pl*R_pl - pow(pl_flat_w/2, 2));

// camini: verifica che nessun raggio rettilineo dalla placca attraversi il foro
ch_bore   = cable_d;
ch_wi     = 1.2;
ch_pk     = lead_t + 0.6;
ch_od     = ch_bore + 2*(ch_wi + ch_pk + 1.6);
function ch_Lmin(off, h) = ch_bore / ((off - anode_r - ch_bore/2) / h);
hv_h      = tube_seated_h - anode_rim_h + top_clear;
lv_h      = anode_rim_h + socket_h + tray_h + lead_t + floor_t;
assert(hv_ch_L >= 1.3*ch_Lmin(hv_off, hv_h), "Camino AT troppo corto");
assert(lv_ch_L >= 1.3*ch_Lmin(lv_off, lv_h), "Camino BT troppo corto");
assert(H <= printer[2] && 2*R_pl <= printer[0], "Non entra nel piano di stampa");

function r_layer(i)   = cup_or + lead_tol/4 + i*lead_sheet;      // raggio interno strato i
function strip_len(i) = 2*PI*(r_layer(i) + lead_sheet/2) - 0.5;
function seam_ang(i)  = 90 + seam_off[i];
function win_pos(i)   = (r_layer(i) + lead_sheet/2) * (win_ang - seam_ang(i)) * PI/180;
function ch_strip(i)  = 2*PI*(ch_bore/2 + ch_wi + 0.3 + i*lead_sheet + lead_sheet/2) - 0.3;

echo(str("Cavita' D ", 2*cav_r, " x ", cav_h, " mm"));
echo(str("Corpo D ", 2*sl_or, " x ", H, " mm; basamento D ", 2*R_pl, " x ", plinth_h + plinth_lip));
echo(str("Piombo: ", lead_n, " fogli da ", lead_sheet, " mm = ", lead_t, " mm"));
echo(str("Centro finestra a z = ", win_z, " mm dal fondo del bicchiere"));
for (i = [0:lead_n-1]) echo(str("Strato ", i+1, ": striscia ", round(strip_len(i)*10)/10, " x ", plate_h,
    ", foro finestra a ", round(win_pos(i)*10)/10, " mm dall'estremita' sinistra"));
echo(str("Camino AT: min ", round(ch_Lmin(hv_off, hv_h)), " mm, usato ", hv_ch_L,
         "; camino BT: min ", round(ch_Lmin(lv_off, lv_h)), " mm, usato ", lv_ch_L));
pb_area = lead_n*plate_h*2*PI*(r_layer(0) + lead_t/2)
        + lead_n*PI*(pow(cav_r - 0.25, 2) + pow(sl_or, 2))
        + lead_n*2*PI*(ch_bore/2 + ch_wi + lead_t/2)*(hv_ch_L + lv_ch_L) + lead_n*900;
echo(str("Piombo totale ~", round(pb_area*lead_sheet*11.35/1000), " g (",
         round(pb_area/1000)/1000, " m2 di foglio)"));

// =====================================================================
module teardrop_y(d, l) {
    rotate([90,0,0]) linear_extrude(l, center=true)
        union() { circle(d=d); rotate(45) square(d/2); }
}
module dhole_y(d, flat, l) {
    rotate([90,0,0]) linear_extrude(l, center=true)
        intersection() {
            circle(d=d);
            if (flat > 0) translate([0, flat/2 - d/2]) square([d, flat], center=true);
            else circle(d=d);
        }
}
module ring(ro, ri, h) { difference() { cylinder(r=ro, h=h); translate([0,0,-1]) cylinder(r=ri, h=h+2); } }

// ------------------------- BICCHIERE INTERNO -------------------------
// Stampare in piedi, 100% riempimento (e' l'isolamento fra AT e piombo).
module cup() {
    difference() {
        union() {
            cylinder(r=cup_or, h=H);
            cylinder(r=sl_or, h=fl_t);      // flangia: sostiene piombo e manicotto
        }
        translate([0,0,floor_t]) cylinder(r=cav_r, h=H);
        // foro cavi BT + fori pilota per il camino sotto
        translate([lv_xy[0], lv_xy[1], -1]) cylinder(d=cable_d, h=floor_t + 2);
        for (a=[0,120,240]) translate([lv_xy[0], lv_xy[1], -1]) rotate(a) translate([ch_od/2 + 3.5, 0, 0])
            cylinder(d=2.6, h=3);
        // membrana della finestra: parete assottigliata dall'interno
        intersection() {
            translate([0, -cup_or, win_z]) teardrop_y(window_d + 2, 2*wall_in + 10);
            cylinder(r=cup_or - membrane_t, h=H);
        }
        // tacche sulla flangia: dove cadono i giunti di ciascuno strato
        for (i=[0:lead_n-1]) rotate(seam_ang(i)) translate([sl_or, 0, -1]) cylinder(d=2, h=fl_t + 2, $fn=12);
        // filo di terra del piombo: foro nella flangia sotto gli strati + canalina
        // sotto la flangia verso l'interno del basamento
        rotate(60) translate([r_layer(0) + 1, 0, -1]) cylinder(d=2, h=fl_t + 2, $fn=12);
        rotate(60) translate([sl_or - 9, -1, -eps]) cube([r_layer(0) + 2 - (sl_or - 9), 2, 1.2]);
    }
}

// ------------------------- MANICOTTO ESTERNO -------------------------
function win_holes() = [[-27,-20], [27,-20], [-27,45], [27,45]];
module sleeve() {
    difference() {
        union() {
            translate([0,0,fl_t]) cylinder(r=sl_or, h=H - fl_t);
            // borchie del modulo finestra fino al piano comune y = -(sl_or + boss_h)
            for (p = win_holes()) translate([p[0], -sl_or/2, win_z + p[1]])
                rotate([90,0,0]) cylinder(d=9, h=sl_or/2 + boss_h);
            // blocchetto microswitch (retro)
            translate([sw_x - 10, sl_or - 3, sw_top - sw_h - 6]) cube([10, sw_len + 7, sw_h + 6]);
            // chiavetta che orienta il coperchio
            translate([key_x - 2, sl_or - 1, H - 10]) cube([4, 3, 10]);
        }
        translate([0,0,-1]) cylinder(r=sl_ir, h=H + 2);
        translate([0, -(sl_ir + sl_or)/2, win_z]) teardrop_y(window_d + 2, wall_out + 4);
        for (p = win_holes())
            let(d = sl_or + boss_h - sqrt(sl_ir*sl_ir - p[0]*p[0]) - 1.2)
            translate([p[0], -(sl_or + boss_h) - eps, win_z + p[1]]) rotate([-90,0,0]) cylinder(d=2.6, h=d);
        for (k = [0,1]) translate([sw_x - 6, sl_or + 3 + (sw_len - sw_pitch)/2 + k*sw_pitch, sw_top - sw_h + 2.9])
            rotate([0,90,0]) cylinder(d=1.8, h=10);
    }
}

// ------------------------- COPERCHIO -------------------------
// Stampare capovolto. N dischi di piombo D = 2*sl_or appoggiati sui bordi
// (biadesivo). Il dito preme il microswitch; la tacca nella gonna lo orienta.
module lid() {
    z0 = H + lead_t;
    difference() {
        union() {
            translate([0,0,z0]) cylinder(r=sl_or + skirt_gap + skirt_w, h=lid_t);
            translate([0,0,skirt_bot]) ring(sl_or + skirt_gap + skirt_w, sl_or + skirt_gap, z0 - skirt_bot + eps);
            translate([sw_x, sl_or + skirt_gap, sw_top + 2]) cube([sw_w, sw_len, skirt_bot - sw_top]);
        }
        translate([hv_xy[0], hv_xy[1], z0 - 1]) cylinder(d=cable_d, h=lid_t + 2);
        for (a=[0,120,240]) translate([hv_xy[0], hv_xy[1], z0 - 1]) rotate(a) translate([ch_od/2 + 3.5, 0, 0])
            cylinder(d=2.6, h=lid_t + 2);
        translate([key_x - 2.5, sl_or - 2, skirt_bot - 1]) cube([5, 8, 12]);
    }
}

// ------------------------- CAMINI PIOMBATI -------------------------
// Tubo con tasca anulare per N strisce di piombo avvolte (aperta dal lato della flangia,
// cosi' il piombo tocca la piastra). Stampare con la flangia sul piatto.
module chimney(L) {
    difference() {
        union() {
            cylinder(d=ch_od + 14, h=3);
            cylinder(d=ch_od, h=L + 2);
        }
        translate([0,0,-1]) cylinder(d=ch_bore, h=L + 4);
        translate([0,0,-eps]) ring(ch_bore/2 + ch_wi + ch_pk, ch_bore/2 + ch_wi, L);
        for (a=[0,120,240]) rotate(a) translate([ch_od/2 + 3.5, 0, -1]) cylinder(d=3.4, h=5);
    }
}
module lv_chimney() chimney(lv_ch_L);

// Passante AT: camino piombato + alette (creepage) + serracavo a vite in cima.
module hv_bushing() {
    L = hv_ch_L + 2;
    difference() {
        union() {
            chimney(hv_ch_L);
            for (z=[6:12:L-14]) translate([0,0,z]) cylinder(d1=ch_od, d2=ch_od + 14, h=7);
            translate([0,0,L]) cylinder(d=16, h=14);
            translate([0,0,L+2]) linear_extrude(12) square([34, 10], center=true);
        }
        translate([0,0,-1]) cylinder(d=ch_bore, h=L + 20);
        translate([0,0,-eps]) ring(ch_bore/2 + ch_wi + ch_pk, ch_bore/2 + ch_wi, hv_ch_L);
        translate([0,0,L + 1]) cylinder(d=cable_d - 1.5, h=20);          // presa sul cavo
        translate([0,0,L]) linear_extrude(15) square([40, 1.6], center=true);
        for (s=[-1,1]) translate([s*12.5, 0, L + 8]) rotate([90,0,0]) cylinder(d=3.4, h=12, center=true);
    }
}

// ------------------------- BASAMENTO CON CONNETTORI -------------------------
// Vaschetta cilindrica con retro piatto per i connettori; il corpo la chiude.
// Stampare cosi' com'e'.
module plinth_2d(o=0) {
    intersection() {
        circle(r=R_pl - o);
        translate([-R_pl, -R_pl]) square([2*R_pl, R_pl + pl_flat_y - o]);
    }
}
module plinth() {
    pf = 3;
    difference() {
        linear_extrude(plinth_h + plinth_lip) plinth_2d();
        translate([0,0,pf]) linear_extrude(plinth_h + plinth_lip) intersection() {
            circle(r=sl_or - 5);
            plinth_2d(3);
        }
        translate([0,0,plinth_h]) cylinder(r=sl_or + 0.5, h=plinth_lip + 1);
        for (c = connectors) {
            translate([c[0], pl_flat_y - 2, c[1]]) dhole_y(c[2], c[3], 10);
            translate([c[0] - 12.5, 30, pf]) cube([25, pl_flat_y - panel_t - 30, plinth_h - pf - 4]);
            translate([c[0], pl_flat_y - 0.6, c[1] + c[2]/2 + 1.5])
                rotate([90,0,180]) linear_extrude(1) text(c[4], size=4, halign="center",
                                                          font="Liberation Sans:style=Bold");
        }
        // tacca fili interblocco
        translate([sw_x - 6, sl_or - 6, plinth_h - 6]) cube([8, 20, 20]);
        // feritoie laterali (zona BT, fuori dallo schermo)
        for (s=[-1,1], k=[-2:2]) translate([s*R_pl, k*12 - 6, plinth_h/2]) cube([26, 5, 24], center=true);
    }
}

// ------------------------- SUPPORTO ZOCCOLO -------------------------
module tray() {
    difference() {
        union() {
            translate([0,0,tray_h-4]) cylinder(d=tray_d, h=4);
            for (a=[90, 210, 330]) rotate(a) translate([tray_d/2 - 6, 0, 0]) cylinder(d=10, h=tray_h);
        }
        translate([0,0,-1]) cylinder(d=socket_hole, h=tray_h + 2);
        for (sx=[-1,1]) translate([sx*socket_mount/2, 0, -1]) cylinder(d=3.4, h=tray_h + 2);
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

module window_frame() {
    difference() {
        translate([-fr_w/2, 0, -fr_bot]) cube([fr_w, fr_t, fr_bot + fr_top]);
        translate([0, fr_t/2, 0]) teardrop_y(window_d + 2, fr_t + 2);
        translate([-23, fr_back, -fr_bot + 2]) cube([46, filter_t, fr_bot + fr_top]);
        translate([-(sh_w + 1)/2, fr_back + filter_t + fr_rib, -fr_bot + 2])
            cube([sh_w + 1, sh_t + 0.6, fr_bot + fr_top]);
        for (p = win_holes()) translate([p[0], fr_t/2, p[1]]) rotate([90,0,0])
            cylinder(d=3.4, h=fr_t + 2, center=true);
        translate([pin_x, fr_back + filter_t + 0.6, fr_top - 8]) rotate([-90,0,0]) cylinder(d=3.2, h=fr_t);
    }
}
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
// Strisce da avvolgere: la x cresce in senso antiorario visto dall'alto;
// allineare il foro alla finestra e il giunto cade sulla tacca della flangia.
module lead_wall(i) {
    difference() {
        square([strip_len(i), plate_h]);
        translate([win_pos(i), win_z - fl_t]) circle(d=window_d);
    }
}
module lead_floor() difference() { circle(r=cav_r - 0.25); translate(lv_xy) circle(d=cable_d); }
module lead_lid()   difference() { circle(r=sl_or);        translate(hv_xy) circle(d=cable_d); }

// ------------------------- ASSIEME -------------------------
module halfcut(cut) {
    if (cut) difference() { children(); translate([-300, 0, -200]) cube([600, 300, 800]); }
    else children();
}
module assembly(cut=false) {
    translate([0,0,-plinth_h]) color("DarkSlateGray") plinth();
    translate([lv_xy[0], lv_xy[1], 0]) mirror([0,0,1]) color("Orange") lv_chimney();
    halfcut(cut) color("SteelBlue", cut ? 1 : 0.4) cup();
    halfcut(cut) color("LightSteelBlue", cut ? 1 : 0.3) sleeve();
    halfcut(cut) for (i = [0:lead_n-1]) color(i % 2 ? "Gray" : "DimGray") {
        translate([0,0,floor_t + i*lead_sheet]) cylinder(r=cav_r - 0.25, h=lead_sheet);
        translate([0,0,fl_t]) ring(r_layer(i) + lead_sheet, r_layer(i), plate_h);
    }
    color("Orange") translate([0,0,floor_t + lead_t]) tray();
    z0 = floor_t + lead_t + tray_h;
    color("Black") translate([0,0,z0]) cylinder(d=32, h=socket_h);
    color("LightCyan", cut ? 1 : 0.4) translate([0,0,z0 + socket_h]) cylinder(d=tube_d - 2, h=tube_seated_h - 8);
    color("Silver") translate([0,0,z0 + socket_h + anode_rim_h]) cylinder(r=anode_r, h=30);
    color("Red") translate([0,0,z0 + socket_h + anode_rim_h]) cylinder(d=tube_d + 6, h=0.8);
    color("Silver") translate([0,0,z0 + socket_h + tube_seated_h - 8]) cylinder(d=9, h=8);
    color("Black") translate([sw_x, sl_or + 3, sw_top - sw_h]) cube([sw_w, sw_len, sw_h]);
    translate([0,0,50]) {
        halfcut(cut) color("SteelBlue", 0.5) lid();
        color("Orange") translate([hv_xy[0], hv_xy[1], H + lead_t + lid_t]) hv_bushing();
    }
    color("Orange") translate([0, -sl_or - boss_h, win_z]) mirror([0,1,0]) window_frame();
}

// ------------------------- SELETTORE -------------------------
if      (part == "assembly")          assembly();
else if (part == "section")           assembly(cut=true);
else if (part == "cup")               cup();
else if (part == "sleeve")            translate([0,0,-fl_t]) sleeve();
else if (part == "lid")               rotate([180,0,0]) lid();
else if (part == "plinth")            plinth();
else if (part == "tray")              rotate([180,0,0]) tray();
else if (part == "lv_chimney")        lv_chimney();
else if (part == "hv_bushing")        hv_bushing();
else if (part == "window_frame")      window_frame();
else if (part == "shutter")           rotate([90,0,0]) shutter();
else if (part == "lead_wall")         lead_wall(layer);
else if (part == "lead_floor")        lead_floor();
else if (part == "lead_lid")          lead_lid();
else if (part == "lead_chimney_hv")   for (i=[0:lead_n-1]) translate([0, i*(hv_ch_L + 5)]) square([ch_strip(i), hv_ch_L]);
else if (part == "lead_chimney_lv")   for (i=[0:lead_n-1]) translate([0, i*(lv_ch_L + 5)]) square([ch_strip(i), lv_ch_L]);
else if (part == "lead_shutter")      square(30);
