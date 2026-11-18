// =====================================================================
//  Banco ottico su profilo Bosch Rexroth 30x30 (cava 8)
//  Parti: PIEDINO e CAVALIERE, entrambi con fori per inserti filettati
//  M4 a caldo (heat-set). Tutte le misure in mm.
//
//  Render:  openscad -D 'part="cavaliere_t"' -o cavaliere_t.stl banco_ottico.scad
//           openscad -D 'part="cavaliere"' -o cavaliere.stl banco_ottico.scad
//           openscad -D 'part="piedino"'   -o piedino.stl   banco_ottico.scad
//
//  Hardware:
//   - inserti a caldo M4 x 8, Ø esterno 5.5 (foro Ø5.2, regolare ins_d)
//   - viti M4 (meglio a galletto/pomello) per il bloccaggio laterale
//   - piedino: vite M6 + dado a T cava 8 per fissarlo al profilo dal basso
// =====================================================================

part = "assembly";   // "cavaliere_t" | "cavaliere" | "piedino" | "assembly"

/* ---------------- Profilo ---------------- */
prof      = 30;      // lato profilo
slot_w    = 8;       // apertura cava
clr       = 0.35;    // gioco per lato (scorrevole). Aumentare se troppo stretto
lip_mid   = 5.5;     // centro della "labbra" piana tra spigolo e cava ((30-8)/2/2)

/* ---------------- Inserto M4 ---------------- */
ins_d     = 5.2;     // foro per inserto M4x8 Ø est. 5.5 (ca. Ø est. - 0.3). Provare!
ins_len   = 8;       // lunghezza inserto
ins_depth = ins_len + 1.0;  // profondità foro cieco
ins_cham  = 0.6;     // smusso d'imbocco

/* ---------------- Cavaliere ---------------- */
cav_len    = 40;     // lunghezza lungo il profilo
cav_top    = 12;     // spessore piastra sopra al profilo
cav_wall   = 8.5;    // spessore fianchi (contiene l'inserto laterale)
cav_skirt  = 14;     // quanto i fianchi scendono lungo il profilo (dall'alto)
cav_key    = true;   // linguetta di guida nella cava superiore
key_w      = slot_w - 0.5;
key_h      = 1.5;

/* ---------------- Cavaliere a T (piccolo, scorre nella cava) ----------
   MISURARE LA CAVA col calibro: le quote interne variano tra serie.       */
ct_len     = 34;     // lunghezza lungo il profilo
ct_w       = 30;     // larghezza (= profilo, a filo)
ct_h       = ins_len; // spessore placchetta = lunghezza inserto (fori passanti)
lip_t      = 2.2;    // spessore labbro della cava (superficie -> sottosquadro)
neck_w     = slot_w - 0.5;   // collo che passa nell'apertura della cava
wing_w     = 13.5;   // larghezza ali della T (larghezza interna cava ~16)
wing_t     = 2.5;    // spessore ali
wing_cham  = 1.2;    // smusso spigoli inferiori ali (fondo cava inclinato)
lock_d     = 4.5;    // foro passante per grano M4 di bloccaggio
lock_off   = 5.5;    // distanza dei grani dalle estremità

/* ---------------- Piedino ---------------- */
pie_len    = 40;     // lunghezza lungo il profilo
pie_width  = 100;    // larghezza totale (trasversale)
pie_base   = 8;      // spessore base sotto al profilo
pie_wall   = 8.5;    // spessore pareti della culla
pie_cradle = 12;     // altezza pareti culla (lascia passare il cavaliere sopra)
pie_wing_t = 6;      // spessore ali di fissaggio
m6_d       = 6.6;    // foro passante vite M6 (dado a T nella cava inferiore)
m6_head_d  = 11;     // svasatura/lamatura testa M6
m6_head_h  = 4;
tab_slot_d = 6.6;    // asole per fissaggio al tavolo (M6)
tab_slot_l = 10;     // lunghezza asola

$fn = 64;
eps = 0.01;
inner = prof + 2*clr;

/* ===================================================================== */

module insert_hole(depth = ins_depth) {
    // foro cieco lungo +Z partendo da z=0 verso il basso (-Z)
    translate([0,0,-depth]) cylinder(d = ins_d, h = depth + eps);
    translate([0,0,-ins_cham]) cylinder(d1 = ins_d, d2 = ins_d + 2*ins_cham, h = ins_cham + eps);
}

module chamfer_box(size, c = 1) {
    // cubo con spigoli verticali smussati
    hull() {
        translate([c,0,0]) cube([size.x-2*c, size.y, size.z]);
        translate([0,c,0]) cube([size.x, size.y-2*c, size.z]);
    }
}

/* ---------------- CAVALIERE ----------------
   Sistema: X trasversale, Y lungo il profilo, Z verso l'alto.
   z=0 = faccia superiore del profilo.                                   */
module cavaliere() {
    W = inner + 2*cav_wall;
    difference() {
        union() {
            translate([-W/2, 0, -cav_skirt])
                chamfer_box([W, cav_len, cav_skirt + clr + cav_top], 1.5);
        }
        // canale per il profilo (con smussi d'ingresso)
        translate([-inner/2, -1, -cav_skirt - 1])
            cube([inner, cav_len + 2, cav_skirt + 1 + clr]);
        // inserto M4 in alto (montaggio supporti / colonnine)
        translate([0, cav_len/2, clr + cav_top]) insert_hole();
        // inserto M4 laterale per vite di bloccaggio (preme sulla parte piana)
        translate([inner/2 + cav_wall, cav_len/2, -lip_mid])
            rotate([0, 90, 0]) insert_hole(cav_wall + 1);
    }
    // linguetta di guida nella cava superiore
    if (cav_key)
        translate([-key_w/2, 3, clr - key_h]) cube([key_w, cav_len - 6, key_h + eps]);
}

/* ---------------- PIEDINO ----------------
   z=0 = faccia inferiore del profilo.                                    */
module piedino() {
    W = inner + 2*pie_wall;
    difference() {
        union() {
            // culla
            translate([-W/2, 0, -pie_base]) cube([W, pie_len, pie_base + pie_cradle]);
            // ali
            translate([-pie_width/2, 0, -pie_base]) chamfer_box([pie_width, pie_len, pie_wing_t], 3);
            // raccordi ala-culla
            for (s = [-1, 1]) hull() {
                translate([s*W/2 - (s>0?0:eps), 0, -pie_base]) cube([eps, pie_len, pie_wing_t + 6]);
                translate([s*(W/2 + 6) - (s>0?0:eps), 0, -pie_base]) cube([eps, pie_len, pie_wing_t]);
            }
        }
        // sede del profilo
        translate([-inner/2, -1, 0]) cube([inner, pie_len + 2, pie_cradle + 1]);
        // smusso d'ingresso in alto
        hull() {
            translate([-inner/2, -1, pie_cradle - 0.01]) cube([inner, pie_len + 2, 0.02]);
            translate([-inner/2 - 1, -1, pie_cradle + 0.01]) cube([inner + 2, pie_len + 2, 0.02]);
        }
        // foro M6 dal basso verso dado a T nella cava inferiore
        translate([0, pie_len/2, -pie_base - 1]) cylinder(d = m6_d, h = pie_base + 2);
        translate([0, pie_len/2, -pie_base - eps]) cylinder(d = m6_head_d, h = m6_head_h);
        // inserti M4 laterali per vite di bloccaggio (sulla parte piana in basso)
        for (s = [-1, 1])
            translate([s*(inner/2 + pie_wall), pie_len/2, lip_mid])
                rotate([0, s*90, 0]) insert_hole(pie_wall + 1);
        // asole per fissaggio al banco/tavolo
        for (s = [-1, 1])
            translate([s*(pie_width/2 - 10), pie_len/2, -pie_base - 1])
                hull() for (dy = [-tab_slot_l/2, tab_slot_l/2])
                    translate([0, dy, 0]) cylinder(d = tab_slot_d, h = pie_wing_t + 2);
    }
}

/* ---------------- CAVALIERE A T ----------------
   Corpo appoggiato sulla faccia superiore del profilo + chiavetta a T che
   scorre nella cava. Inserto M4 al centro per la colonnina; due inserti
   M4 alle estremità per grani che spingono sul fondo cava: la T viene
   tirata contro i labbri e il cavaliere si blocca.
   z=0 = faccia superiore del profilo. Si infila dall'estremità del profilo. */
module cavaliere_t() {
    neck_h = lip_t + 0.3;
    difference() {
        union() {
            translate([-ct_w/2, 0, 0]) chamfer_box([ct_w, ct_len, ct_h], 1.5);
            // collo
            translate([-neck_w/2, 0, -neck_h]) cube([neck_w, ct_len, neck_h + eps]);
            // ali della T (sezione trapezia)
            hull() {
                translate([-wing_w/2, 0, -neck_h - wing_t + wing_cham]) cube([wing_w, ct_len, wing_t - wing_cham]);
                translate([-wing_w/2 + wing_cham, 0, -neck_h - wing_t]) cube([wing_w - 2*wing_cham, ct_len, wing_t]);
            }
        }
        // inserto M4 per la colonnina, al centro
        // (passante: una vite troppo lunga finisce nella cava, nessun danno)
        translate([0, ct_len/2, ct_h]) insert_hole(ct_h + 1);
        // inserti M4 + foro passante per i grani di bloccaggio
        for (y = [lock_off, ct_len - lock_off]) translate([0, y, 0]) {
            translate([0, 0, ct_h]) insert_hole(ct_h + 1);
            translate([0, 0, -20]) cylinder(d = lock_d, h = ct_h + 20);
        }
    }
}

/* ---------------- profilo (solo visualizzazione) ---------------- */
module profilo(len = 300) {
    color("silver") difference() {
        translate([-prof/2, 0, 0]) cube([prof, len, prof]);
        for (r = [0:90:270])
            translate([0, -1, prof/2]) rotate([0, r, 0])
                translate([-slot_w/2, 0, prof/2 - 9]) cube([slot_w, len + 2, 10]);
        translate([0, -1, prof/2]) rotate([-90, 0, 0]) cylinder(d = 6.8, h = len + 2);
    }
}

/* ---------------- Selezione / orientamento di stampa ---------------- */
if (part == "cavaliere_t") {
    // stampa in piedi (asse del profilo verticale): la sezione a T sta nel
    // piano dei layer -> nessun supporto e ali robuste
    rotate([-90, 0, 0]) translate([0, -ct_len, 0]) cavaliere_t();
} else if (part == "cavaliere") {
    // stampa capovolto: faccia superiore sul piatto, nessun supporto
    rotate([180, 0, 0]) translate([0, -cav_len/2, -(clr + cav_top)]) cavaliere();
} else if (part == "piedino") {
    translate([0, -pie_len/2, pie_base]) piedino();
} else {
    profilo();
    for (y = [10, 250]) translate([0, y, 0]) piedino();
    translate([0, 90, prof]) cavaliere();
    for (y = [150, 200]) translate([0, y, prof]) cavaliere_t();
}
