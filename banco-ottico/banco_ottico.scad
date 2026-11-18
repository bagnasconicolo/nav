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
//   - inserti a caldo M4 x 8, Ø esterno 5.5 (foro Ø5.0, regolare ins_d)
//   - viti M4 (meglio a galletto/pomello) per il bloccaggio laterale
//   - piedino: vite M6 + dado a T cava 8 per fissarlo al profilo dal basso
// =====================================================================

part = "assembly";   // "cavaliere_t" | "cavaliere" | "piedino" | "piedino_culla" | "laser" | "assembly"

/* ---------------- Profilo ---------------- */
prof      = 30;      // lato profilo
slot_w    = 8;       // apertura cava
clr       = 0.35;    // gioco per lato (scorrevole). Aumentare se troppo stretto
lip_mid   = 5.5;     // centro della "labbra" piana tra spigolo e cava ((30-8)/2/2)

/* ---------------- Inserto M4 ---------------- */
ins_d     = 5.0;     // foro per inserto M4x8 Ø est. 5.5
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
ct_len     = 44;     // lunghezza lungo il profilo
ct_w       = 30;     // larghezza (= profilo, a filo)
ct_h       = 4;      // spessore placchetta
tur_s      = 14;     // lato torretta quadrata centrale (inserto colonnina)
tur_slope  = false;  // true: un lato a 45° (solo per stampa in piedi)
tur_h      = ins_len - ct_h;  // altezza torretta sopra la placchetta
lip_t      = 2.2;    // spessore labbro della cava (superficie -> sottosquadro)
neck_w     = slot_w - 0.5;   // collo che passa nell'apertura della cava
wing_w     = 13.5;   // larghezza ali della T (larghezza interna cava ~16)
wing_t     = 2.5;    // spessore ali
wing_cham  = 1.2;    // smusso spigoli inferiori ali (fondo cava inclinato)
lock_off   = 5;      // distanza dei grani dalle estremità

/* ---------------- Supporto laser Ø12 (su torretta del cavaliere a T) ---- */
las_d     = 12;      // diametro corpo laser (misurare col calibro!)
las_clr   = 0.3;     // gioco radiale nel V
las_len   = 22;      // lunghezza del supporto (laser 30 mm: sporge 8 mm)
las_w     = 25;      // larghezza base
las_wall  = 6;       // parete sopra al laser (filetto vite di serraggio)
las_floor = 3;       // fondo sotto la testa della vite di fissaggio
las_head_d= 8;       // lamatura testa vite M4 (TCEI Ø7)
las_head_h= 4;
las_pocket= 2;       // profondità sede che calza la torretta quadrata
m4_clear  = 4.4;     // foro passante M4
m4_tap    = 3.4;     // foro M4 autofilettante

/* ---------------- Piedino ad arco (design) ----------------
   Sezione trapezoidale cava, raccordata; chiavetta a T nella cava
   inferiore del profilo; vite M4 autofilettante dal basso per il bloccaggio.            */
pa_len   = 25;       // spessore lungo il profilo
pa_h     = 20;       // altezza (tavolo -> faccia inferiore profilo)
pa_base  = 72;       // larghezza all'appoggio
pa_top   = 30;       // larghezza in alto (= profilo)
pa_t     = 5;        // spessore pareti
pa_r     = 5;        // raggio raccordi esterni
pa_ri    = 8;        // raggio raccordo interno (volta)
pa_tap_d = 3.4;      // foro per autofilettare la vite M4 (PLA/PETG: 3.3-3.5)

/* ---------------- Piedino (versione a culla) ---------------- */
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
   Placchetta sottile appoggiata sul profilo + chiavetta a T nella cava.
   Torretta centrale con inserto M4 per la colonnina; due inserti M4 alle
   estremità con foro fino al fondo della T: i grani spingono sul fondo
   cava, la T viene tirata contro i labbri e il cavaliere si blocca.
   z=0 = faccia superiore del profilo. Si infila dall'estremità del profilo. */
module cavaliere_t() {
    neck_h = lip_t + 0.3;
    t_bot  = -neck_h - wing_t;          // fondo della T
    difference() {
        union() {
            translate([-ct_w/2, 0, 0]) chamfer_box([ct_w, ct_len, ct_h], 1.5);
            // torretta centrale quadrata; il lato +Y (verso il piatto in
            // stampa) è inclinato a 45° per non avere sbalzi
            translate([0, ct_len/2, ct_h - eps]) hull() {
                translate([-tur_s/2, -tur_s/2, 0]) cube([tur_s, tur_s, tur_h + eps]);
                if (tur_slope)
                    translate([-tur_s/2, -tur_s/2, 0]) cube([tur_s, tur_s + tur_h, eps]);
            }
            // collo
            translate([-neck_w/2, 0, -neck_h]) cube([neck_w, ct_len, neck_h + eps]);
            // ali della T (sezione trapezia)
            hull() {
                translate([-wing_w/2, 0, -neck_h - wing_t + wing_cham]) cube([wing_w, ct_len, wing_t - wing_cham]);
                translate([-wing_w/2 + wing_cham, 0, t_bot]) cube([wing_w - 2*wing_cham, ct_len, wing_t]);
            }
        }
        // inserto M4 per la colonnina, nella torretta (cieco, fino alla base placchetta)
        translate([0, ct_len/2, ct_h + tur_h]) insert_hole(ct_h + tur_h);
        // inserti M4 laterali per i grani: foro fino al fondo della T
        for (y = [lock_off, ct_len - lock_off])
            translate([0, y, ct_h]) insert_hole(ct_h - t_bot + 1);
    }
}

/* ---------------- PIEDINO AD ARCO ----------------
   z=0 = piano del tavolo; il profilo appoggia a z=pa_h.                  */
module arco2d() {
    k  = (pa_base - pa_top) / 2 / pa_h;          // pendenza delle gambe
    ext = 2 * pa_r;                              // prolungo sotto al piano
    tr = [[-pa_base/2 - k*ext, -ext], [pa_base/2 + k*ext, -ext],
          [pa_top/2, pa_h], [-pa_top/2, pa_h]];
    intersection() {
        difference() {
            offset(r = pa_r) offset(delta = -pa_r) polygon(tr);
            // volta interna, aperta in basso
            hull() for (dz = [0, -2*pa_h])
                translate([0, dz])
                    offset(r = pa_ri) offset(delta = -pa_ri - pa_t) polygon(tr);
        }
        // taglio a z=0 (piedi piatti, appoggio pieno) e punte spuntate
        // (niente spigoli a lama: robuste, non si scheggiano)
        translate([-pa_base/2 + 2.5, 0]) square([pa_base - 5, pa_h + 1]);
    }
}

module t_key_up(len) {
    // collo + ali della T rivolti verso +Z a partire da z=0
    neck_h = lip_t + 0.3;
    translate([-neck_w/2, 0, -eps]) cube([neck_w, len, neck_h + 2*eps]);
    hull() {
        translate([-wing_w/2, 0, neck_h]) cube([wing_w, len, wing_t - wing_cham]);
        translate([-wing_w/2 + wing_cham, 0, neck_h]) cube([wing_w - 2*wing_cham, len, wing_t]);
    }
}

module piedino_arco() {
    neck_h = lip_t + 0.3;
    difference() {
        union() {
            translate([0, pa_len, 0]) rotate([90, 0, 0])
                linear_extrude(pa_len) arco2d();
            translate([0, 0, pa_h]) t_key_up(pa_len);
        }
        // foro M4 da filettare con la vite stessa (niente inserto): dal basso
        // attraversa traversa e T; la vite spinge sul fondo della cava e
        // blocca il piedino
        translate([0, pa_len/2, pa_h - pa_t - eps]) {
            cylinder(d = pa_tap_d, h = pa_t + neck_h + wing_t + 1);
            cylinder(d1 = pa_tap_d + 1.2, d2 = pa_tap_d, h = 0.6);   // invito
        }
    }
}

/* ---------------- SUPPORTO LASER ----------------
   Sede a V (2 linee di contatto) + vite M4 dall'alto che preme il laser:
   il laser si centra da solo. Sotto, una sede quadrata calza la torretta
   del cavaliere (niente rotazioni, asse allineato al profilo).
   Fissaggio: vite M4 TCEI nell'inserto della torretta; si stringe con una
   chiave a brugola da 3 passando dal foro della vite di serraggio.
   z=0 = faccia superiore della torretta; Y = asse del laser.             */
las_r  = las_d/2 + las_clr;
las_cz = las_pocket + las_floor + las_head_h + 0.5 + las_r*sqrt(2);  // centro arco
las_axis = las_cz - las_clr*sqrt(2);   // asse reale del laser appoggiato nel V
echo(str("Asse laser sopra la torretta: ", las_axis, " mm; sopra il profilo: ",
         las_axis + ct_h + tur_h, " mm"));

module laser2d() {
    difference() {
        hull() {
            offset(r = 3) offset(delta = -3) translate([-las_w/2, 0]) square([las_w, las_cz]);
            translate([0, las_cz]) circle(r = las_r + las_wall);
        }
        hull() {
            translate([0, las_cz]) circle(r = las_r);
            translate([0, las_cz - las_r*sqrt(2)]) square(0.01, center = true);
        }
    }
}

module supporto_laser() {
    difference() {
        translate([0, las_len, 0]) rotate([90, 0, 0]) linear_extrude(las_len) laser2d();
        // sede per la torretta
        sp = tur_s + 0.3;
        translate([-sp/2, las_len/2 - sp/2, -eps]) cube([sp, sp, las_pocket + eps]);
        // fissaggio alla torretta
        translate([0, las_len/2, -1]) cylinder(d = m4_clear, h = las_cz);
        translate([0, las_len/2, las_pocket + las_floor]) cylinder(d = las_head_d, h = las_cz);
        // vite di serraggio dall'alto (autofilettante), coassiale: ci passa
        // la brugola per stringere la vite di fissaggio
        translate([0, las_len/2, las_cz]) cylinder(d = m4_tap, h = las_r + las_wall + 1);
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
    // stampa orizzontale capovolto: faccia della torretta sul piatto
    // (piana per la colonnina), T verso l'alto, fori inserti verticali.
    // Supporti (tree, solo dal piatto) sotto la placchetta attorno alla torretta.
    rotate([180, 0, 0]) translate([0, -ct_len/2, -(ct_h + tur_h)]) cavaliere_t();
} else if (part == "cavaliere") {
    // stampa capovolto: faccia superiore sul piatto, nessun supporto
    rotate([180, 0, 0]) translate([0, -cav_len/2, -(clr + cav_top)]) cavaliere();
} else if (part == "piedino") {
    // stampa in piedi sulla faccia frontale: sezione nel piano dei layer,
    // nessun supporto
    rotate([90, 0, 0]) translate([0, 0, 0]) piedino_arco();
} else if (part == "laser") {
    // stampa in piedi sulla faccia frontale: V e foro nel piano dei layer
    rotate([90, 0, 0]) supporto_laser();
} else if (part == "piedino_culla") {
    translate([0, -pie_len/2, pie_base]) piedino();
} else {
    profilo();
    for (y = [0, 300 - pa_len]) translate([0, y, -pa_h]) piedino_arco();
    translate([0, 90, prof]) cavaliere();
    for (y = [150, 200]) translate([0, y, prof]) cavaliere_t();
    translate([0, 200 + ct_len/2 - las_len/2, prof + ct_h + tur_h]) supporto_laser();
    color("silver") translate([0, 200 + ct_len/2 - 15, prof + ct_h + tur_h + las_axis])
        rotate([-90, 0, 0]) cylinder(d = las_d, h = 30);
}
