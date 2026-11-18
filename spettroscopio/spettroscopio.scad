// =====================================================================
//  SPETTROSCOPIO PER SMARTPHONE — reticolo da DVD/CD in trasmissione
//  Modello parametrico OpenSCAD (>= 2021.01). Unità: mm, nm, gradi.
//
//  Schema ottico (fenditura -> collimatore -> reticolo -> camera a infinito)
//
//      fenditura (lame)          lente f=45 + stop Ø8      reticolo DVD
//   ─────|·|───────────────────────(  )──|──────────────────── ╱ ──> camera
//        \___ tubo inclinato di α = asin(λc/d) rispetto all'asse camera ___/
//
//  Il reticolo è parallelo al sensore: la λc (550 nm) esce lungo l'asse
//  ottico della camera, lo spettro 380–750 nm cade a ±14° (DVD) nel campo.
//
//  Selezione pezzo:  openscad -D 'part="base"' -o base.stl spettroscopio.scad
//  part = assembly | exploded | section | base | tube | cap | slit_plate | cassette |
//         back_plate | jaw | knob | plate_all
// =====================================================================

part = "assembly";

/* [Ottica] */
grating_pitch = 740;    // nm  (DVD-R: 740, CD-R: 1600)
lambda_c      = 550;    // nm  lunghezza d'onda al centro del sensore
grating_t     = 0.6;    // mm  spessore del pezzo di reticolo (DVD 0.6, CD 1.2)
// Default: PATIKIL "Convex Lens 25 mm OD, 6.5 mm H, borosilicato, f 36 mm" (Amazon)
//          -> piano-convessa, lato piatto verso la fenditura.
// Lente Cardboard: lens_type="bcx", lens_n=1.49, lens_ct=5.6, lens_f=45
lens_type     = "pcx";  // "pcx" piano-convessa | "bcx" biconvessa simmetrica
lens_d        = 25.0;   // mm  diametro
lens_ct       = 6.5;    // mm  spessore al centro (MISURARE)
lens_f        = 36.0;   // mm  focale efficace (MISURARE)
lens_n        = 1.474;  //     indice (borosilicato 1.474, PMMA 1.49, BK7/K9 1.517)
stop_d        = 8.0;    // mm  diaframma d'apertura dopo la lente
slit_len      = 6.0;    // mm  altezza utile della fenditura

/* [Lame della fenditura] */
blade_w = 14.0;         // mm  (lungo la fenditura)
blade_h = 9.0;          // mm  (perpendicolare)
blade_t = 0.10;         // mm  lama da rasoio bilama 0.10

/* [Telefono] */
phone_t   = 8.3;        // mm  spessore (con eventuale cover)
cam_dy    = 12.0;       // mm  centro obiettivo principale -> bordo superiore
felt_c    = 0.6;        // mm  spessore compresso del feltro adesivo sulla ganascia
post_dx   = 22.0;       // mm  semi-interasse dei due perni di riferimento

/* [Inserti filettati a caldo M3] */
ins_d    = 4.0;         // mm  foro per inserto M3 (Ruthex/CNC Kitchen standard)
ins_l    = 4.0;         // mm  lunghezza inserto (M3x4)
m3_clear = 3.4;

/* [O-ring NBR 22x1.5 per frizione/fuoco] */
or_cs = 1.5;
or_id = 22.0;

/* [Stampa] */
fit = 0.15;             // gioco radiale accoppiamenti scorrevoli
$fn = 120;

// ------------------------------------------------------------------
// Grandezze derivate (non modificare)
// ------------------------------------------------------------------
alpha  = asin(lambda_c / grating_pitch);      // inclinazione del tubo
echo(str("alpha (inclinazione tubo) = ", alpha, " deg"));

tube_r   = 14.5;                 // raggio esterno tubo/cappuccio
neck_r   = 12.5;                 // raggio esterno collo (sotto il cappuccio)
lens_cb_r = lens_d/2 + 0.1;      // sede lente
groove_root_r = (or_id*1.03)/2;  // fondo gola O-ring (3% di stiro)
groove_w = or_cs + 0.5;

// --- base (naso) ---
sp_r   = 15.0;   sp_h = 6.0;     // codolo baionetta
sh_r   = 17.0;                   // spalla d'appoggio
lug_h  = 2.0;    lug_ro = 16.6;
lug_a  = [90, 210, 330];  lug_w = [34, 22, 22];   // asimmetrico: un solo verso
twist  = 30;                     // rotazione di chiusura
z_c    = 9.5;    cas_t = 2.0;    // cassetta reticolo
z_g    = z_c + cas_t - grating_t/2;               // piano del reticolo
s_f    = 14.0;                   // distanza reticolo -> faccia di appoggio tubo
boss_h = 6.0;
mask_t = 1.2;  win_y = 9;  win_x = 7;             // finestra sopra la camera

// --- tubo (coordinata t lungo l'asse, t=0 sulla faccia della base) ---
// geometria della lente ricavata da f, n, spessore (lente sottile per R)
lens_R   = (lens_type == "pcx" ? 1 : 2) * lens_f * (lens_n - 1);
function sag(r) = lens_R - sqrt(lens_R*lens_R - r*r);
bulge_b  = sag(lens_d/2);                          // sporgenza lato base (curvo)
bulge_s  = lens_type == "pcx" ? 0 : sag(lens_d/2); // sporgenza lato fenditura
lens_edge_t = lens_ct - bulge_b - bulge_s;
r_k      = lens_d/2 - 0.8;                         // anello di contatto sul lato curvo
function dpt(r) = bulge_b - sag(r);                // profondità superficie curva sotto il bordo
t_r0     = boss_h + dpt(r_k);                      // piano del bordo lente lato base
t_seat   = t_r0 + lens_edge_t - 0.1;               // battuta della faccia lato fenditura (0.1 di precarico)
t_vs     = t_seat + bulge_s;                       // vertice lato fenditura
// distanza focale anteriore (dal vertice lato fenditura), lente spessa
ffd      = lens_f * (1 - (lens_n - 1) * lens_ct / (lens_n * lens_R));
t_slit   = t_vs + ffd;                             // fenditura nel fuoco
t_stop   = t_seat + bulge_s + 0.4;
t_lc     = t_r0 + (lens_edge_t)/2;                 // (solo per la vista)
echo(str("lente: R=", lens_R, " bordo=", lens_edge_t, " sporgenza=", bulge_b, " FFD=", ffd));
assert(lens_edge_t > 0.3, "spessore lente incoerente con f e n: misura lens_ct/lens_f");
// --- cappuccio (coordinata c, c=0 faccia esterna) ---
clamp_t  = 2.0;
c_slit   = clamp_t + blade_t/2;
c_bay    = clamp_t + blade_t + 0.02;
win_cap  = [slit_len, 2.4];
r_apex   = norm(win_cap)/2 + 0.3;
c_apex   = c_bay + 1.0;
cap_bore = neck_r + fit;
c_cone   = c_apex + (cap_bore - r_apex);          // base del cono interno
cap_len  = 26.0;
focus_gap = 3.0;                                  // corsa ±3 mm
t_top    = t_slit - (c_cone + focus_gap - c_slit);// estremità del tubo
neck_len = 15.0;
t_neck   = t_top - neck_len;
r_main   = tube_r - 1.6;
r_neck_bore = 10.0;
use_main = (t_neck - 4.3 - t_stop) > (r_main - stop_d/2);   // tubo lungo: camera larga
r_after  = use_main ? r_main : r_neck_bore;
t_baffle = max(t_neck + 5, t_stop + (r_after - stop_d/2) + 2);
echo(str("lunghezza tubo = ", t_top, " mm; fenditura a t = ", t_slit));

// envelope del fascio fenditura->stop (per i diaframmi)
function env(t) = slit_len/2 + (stop_d/2 - slit_len/2)*(t_slit - t)/(t_slit - t_stop) + 0.8;

// ------------------------------------------------------------------
// utilità
// ------------------------------------------------------------------
module along_axis(s=0) {             // frame del tubo nel frame della base
    translate([0,0,z_g]) rotate([alpha,0,0]) translate([0,0,s]) children();
}
module ring(r1, r2, h) difference() { cylinder(r=r2, h=h); translate([0,0,-1]) cylinder(r=r1, h=h+2); }
module sector(r, a0, a1, h) {        // settore angolare pieno
    n = max(2, ceil(abs(a1-a0)/4));
    linear_extrude(h) polygon(concat([[0,0]],
        [for (i=[0:n]) r*[cos(a0+(a1-a0)*i/n), sin(a0+(a1-a0)*i/n)]]));
}
module funnel(t_b, r_ap, R, k=1.5) { // diaframma a imbuto, stampabile a 45°
    rotate_extrude() polygon([[r_ap, t_b], [r_ap+k, t_b], [R+0.01, t_b + R - r_ap - k],
                              [R+0.01, t_b + R - r_ap]]);
}
// gola O-ring con un fianco a 45° (chamfer_low=true: smusso dal lato t0)
module oring_groove(t0, r_out, chamfer_low=true) {
    d = r_out + 1 - groove_root_r;
    rotate_extrude() polygon(chamfer_low
        ? [[groove_root_r, t0], [groove_root_r, t0 + groove_w], [r_out + 1, t0 + groove_w], [r_out + 1, t0 - d]]
        : [[groove_root_r, t0], [groove_root_r, t0 + groove_w], [r_out + 1, t0 + groove_w + d], [r_out + 1, t0]]);
}
module insert_hole(depth = ins_l + 1) {   // foro dritto, cieco, senza smusso
    translate([0,0,-depth]) cylinder(d=ins_d, h=depth+0.01, $fn=40);
}

module lens_solid() {   // nel frame del tubo
    intersection() {
        translate([0,0,t_r0 - bulge_b]) cylinder(r=lens_d/2, h=lens_ct);
        translate([0,0,t_r0 - bulge_b + lens_R]) sphere(r=lens_R, $fn=96);
        if (lens_type == "bcx") translate([0,0,t_seat + bulge_s - lens_R]) sphere(r=lens_R, $fn=96);
    }
}

// ==================================================================
//  1. BASE (naso): baionetta, camera oscura, cassetta, appoggio tubo
//     Stampa: faccia telefono sul piatto, senza supporti.
// ==================================================================
module base() {
    difference() {
        union() {
            // codolo + alette baionetta
            cylinder(r=sp_r, h=sp_h + 0.5);
            for (i=[0:2]) rotate(lug_a[i] - lug_w[i]/2)
                difference() { sector(lug_ro, 0, lug_w[i], lug_h);
                               translate([0,0,-1]) cylinder(r=sp_r-0.5, h=lug_h+2); }
            // corpo: loft fra spalla circolare e faccia d'appoggio inclinata
            hull() {
                translate([0,0,sp_h]) cylinder(r=sh_r, h=1);
                along_axis(s_f - 0.01) cylinder(r=tube_r, h=0.01);
            }
            // perno con O-ring che entra nel tubo e trattiene la lente
            along_axis(s_f - 0.01) cylinder(r=lens_cb_r - 0.1, h=boss_h + 0.01);
        }
        // gola O-ring sul perno
        along_axis(s_f) oring_groove(1.2, lens_cb_r - 0.1, false);
        // camera oscura: tronco di cono a 48° (nessun ponte)
        translate([0,0,mask_t]) cylinder(r1=13.2, r2=7.0, h=z_c - mask_t + 0.01);
        // finestra-maschera sopra l'obiettivo (trappola dell'ordine zero)
        translate([-win_x/2, -win_y/2, -1]) cube([win_x, win_y, mask_t + 2]);
        // sede cassetta, aperta su +x
        translate([-9.0, -8.9, z_c]) cube([40, 17.8, cas_t + 0.2]);
        // canale luce lungo l'asse, sopra la cassetta
        intersection() {
            along_axis(-12) cylinder(r=6, h=s_f + boss_h + 13);
            translate([-50,-50, z_c + cas_t + 0.2 - 0.01]) cube(100);
        }
        // spazio per la convessità della lente in cima al perno
        // cavità che segue la superficie curva: la lente tocca solo uno spigolo a r_k
        along_axis(s_f + boss_h) rotate_extrude($fn=96) polygon(concat(
            [[0, 0.5], [r_k, 0.5]],
            [for (i=[0:40]) let(r = r_k*(1 - i/40))
                [r, -min(boss_h - 0.6, dpt(r) - dpt(r_k) + min(0.4, r_k - r))]]));
        // tacca indice (allineamento baionetta) sulla spalla
        translate([0, sh_r - 0.6, sp_h + 0.8]) rotate([-90,0,0]) cylinder(d=1.0, h=3, $fn=16);
    }
}

// ==================================================================
//  2. CASSETTA del reticolo (intercambiabile)  — stampa piatta
// ==================================================================
module cassette() {
    gw = 15.0;  // lato del pezzo di DVD/CD
    difference() {
        union() {
            translate([-8.5, -8.7, 0]) cube([8.5 + 21.5, 17.4, cas_t]);
            // linguetta di presa
            translate([19.0, -8.7, 0]) cube([2.5, 17.4, cas_t + 1.6]);
        }
        translate([-gw/2, -gw/2, cas_t - grating_t - 0.1]) cube([gw + 0.3, gw + 0.3, 2]);
        translate([-4.5, -6.0, -1]) cube([9, 12, 5]);               // apertura utile
        // freccia incisa: le tracce del DVD devono correre lungo x (‖ fenditura)
        translate([12, 0, cas_t - 0.4]) linear_extrude(1)
            polygon([[-3,-0.4],[1,-0.4],[1,-1.6],[3.5,0],[1,1.6],[1,0.4],[-3,0.4]]);
    }
}

// ==================================================================
//  3. TUBO collimatore — stampa con l'estremità della fenditura in basso
// ==================================================================
module tube() {
    difference() {
        union() {
            cylinder(r=tube_r, h=t_neck - 2);
            translate([0,0,t_neck - 2]) cylinder(r1=tube_r, r2=neck_r, h=2);   // smusso 45°
            cylinder(r=neck_r, h=t_top);
        }
        // sede lente + O-ring della base
        translate([0,0,-1]) cylinder(r=lens_cb_r, h=t_seat + 1);
        // spazio per la convessità lente
        cylinder(r=lens_cb_r - 1.1, h=t_stop + 0.01);
        if (use_main) {
            translate([0,0,t_stop]) cylinder(r1=lens_cb_r - 1.1, r2=r_main, h=r_main - lens_cb_r + 1.1);
            // camera principale, raccordo a 45° e collo
            translate([0,0,t_stop + 1.3]) cylinder(r=r_main, h=t_neck - 4.3 - t_stop);
            translate([0,0,t_neck - 3 - 0.01]) cylinder(r1=r_main, r2=r_neck_bore, h=r_main - r_neck_bore + 0.2);
        }
        translate([0,0,use_main ? t_neck - 0.01 : t_stop]) cylinder(r=r_neck_bore, h=t_top);
        // gola O-ring del fuoco
        oring_groove(t_top - 5.5, neck_r);
        // tacca indice di rotazione
        translate([0, tube_r, t_neck - 8]) cube([0.5, 1.2, 10], center=true);
    }
    // diaframma d'apertura (stop) a imbuto e diaframma anti-luce diffusa
    intersection() {
        union() {
            funnel(t_stop, stop_d/2, r_after);
            funnel(t_baffle, env(t_baffle), r_neck_bore);
        }
        cylinder(r=tube_r - 0.5, h=t_top);
    }
}

// ==================================================================
//  4. CAPPUCCIO della fenditura (fuoco + rotazione a frizione su O-ring)
//     Stampa: manicotto in basso, faccia esterna in alto.
// ==================================================================
ins_x = 10.5;
module cap() {
    difference() {
        cylinder(r=tube_r, h=cap_len);
        // smusso estetico 0.6 sul bordo esterno
        translate([0,0,-0.01]) difference() {
            cylinder(r=tube_r + 1, h=0.6);
            cylinder(r1=tube_r - 0.6, r2=tube_r, h=0.6);
        }
        // sede del disco di serraggio
        translate([0,0,-1]) cylinder(r=12.15, h=clamp_t + 1);
        // vano lame
        translate([-blade_w/2 - 0.2, -(blade_h + 0.3), -1]) cube([blade_w + 0.4, 2*(blade_h + 0.3), c_bay + 1]);
        // finestra della fenditura
        translate([-win_cap[0]/2, -win_cap[1]/2, 0]) cube([win_cap[0], win_cap[1], c_apex + 0.1]);
        // cono interno (baffle, nessun ponte)
        translate([0,0,c_apex]) cylinder(r1=r_apex, r2=cap_bore, h=c_cone - c_apex + 0.01);
        // manicotto
        translate([0,0,c_cone]) cylinder(r=cap_bore, h=cap_len);
        // inserti M3 per il disco di serraggio
        for (sx=[-1,1]) translate([sx*ins_x, 0, clamp_t]) mirror([0,0,1]) insert_hole();
        // tacca indice
        translate([0, tube_r, cap_len - 3]) cube([0.5, 1.2, 8], center=true);
    }
}

// ==================================================================
//  5. DISCO di serraggio lame (viti M3x6 svasate) — stampa piatta
// ==================================================================
module slit_plate() {
    difference() {
        cylinder(r=12.0, h=clamp_t);
        // finestra con svaso a V verso l'esterno
        hull() {
            translate([-slit_len/2 - 0.5, -0.6, clamp_t - 0.01]) cube([slit_len + 1, 1.2, 0.01]);
            translate([-slit_len/2 - 2.5, -2.6, -0.01]) cube([slit_len + 5, 5.2, 0.01]);
        }
        for (sx=[-1,1]) translate([sx*ins_x, 0, 0]) {
            translate([0,0,-1]) cylinder(d=m3_clear, h=5, $fn=32);
            translate([0,0,-0.01]) cylinder(d1=6.4, d2=m3_clear, h=(6.4-m3_clear)/2, $fn=32);
        }
    }
}

// ==================================================================
//  6. PIASTRA posteriore + anello baionetta — stampa lato telefono giù
//     Frame telefono: z=0 dorso, y verso il bordo superiore, (0,0) obiettivo
// ==================================================================
tp = 2.4;  ring_h = 6.4;  ring_ro = 19.0;  bore_r = sp_r + fit;
post_r = 4.5;
y_post = cam_dy + post_r;           // i perni toccano il bordo superiore
module back_plate() {
    difference() {
        union() {
            hull() {
                cylinder(r=ring_ro, h=tp);
                for (sx=[-1,1]) translate([sx*post_dx, y_post, 0]) cylinder(r=post_r + 1.0, h=tp);
            }
            cylinder(r=ring_ro, h=ring_h);
        }
        translate([0,0,-1]) cylinder(r=bore_r, h=ring_h + 2);
        // sottosquadro per le alette (percorso di rotazione)
        for (i=[0:2]) rotate(lug_a[i] - lug_w[i]/2 - 1)
            translate([0,0,-1]) sector(lug_ro + 0.35, 0, lug_w[i] + twist + 2, 1 + 0.4 + lug_h + 0.15);
        // tacche d'ingresso
        for (i=[0:2]) rotate(lug_a[i] + twist - lug_w[i]/2 - 1)
            translate([0,0,-1]) sector(lug_ro + 0.35, 0, lug_w[i] + 2, ring_h + 2);
        // fori viti
        for (sx=[-1,1]) translate([sx*post_dx, y_post, -1]) cylinder(d=m3_clear, h=tp + 2, $fn=32);
        // tacca indice
        translate([0, ring_ro - 0.6, ring_h - 0.01]) cylinder(d=1.0, h=1, $fn=16);
    }
}

// ==================================================================
//  7. GANASCIA lato schermo con due perni (riferimento sul bordo)
//     Stampa: lastra sul piatto, perni in alto.
// ==================================================================
jaw_t = 2.4;
module jaw() {
    h_post = phone_t + felt_c;
    difference() {
        union() {
            hull() {
                for (sx=[-1,1]) translate([sx*post_dx, y_post, 0]) cylinder(r=post_r + 1.0, h=jaw_t);
                for (sx=[-1,1]) translate([sx*(post_dx - 2), cam_dy - 8, 0]) cylinder(r=3, h=jaw_t);
            }
            for (sx=[-1,1]) translate([sx*post_dx, y_post, 0]) cylinder(r=post_r, h=jaw_t + h_post);
        }
        for (sx=[-1,1]) translate([sx*post_dx, y_post, jaw_t + h_post]) insert_hole(ins_l + 2);
    }
}

// ==================================================================
//  8. POMELLO per vite M3x8 a testa cilindrica (testa piantata a pressione)
// ==================================================================
module knob() {
    difference() {
        intersection() {
            cylinder(r=5.5, h=6);
            cylinder(r1=5.5 - 0.6 + 6, r2=5.5 - 0.6, h=6);      // smusso superiore
        }
        for (i=[0:23]) rotate(i*15) translate([5.75, 0, -1]) cylinder(r=0.55, h=8, $fn=12);
        translate([0,0,-0.01]) cylinder(d=5.45, h=3.2, $fn=6*8);  // testa ISO 4762
        translate([0,0,-1]) cylinder(d=m3_clear, h=5, $fn=24);
    }
}

// ==================================================================
//  ASSIEME (anteprima)
// ==================================================================
show_phone = true;
module assembly(ex = 0) {   // ex > 0: vista esplosa
    // telefono (fantasma)
    if (show_phone) color([0.15,0.15,0.17,0.35]) translate([-36, cam_dy - 150, -phone_t]) cube([72, 150, phone_t]);
    color([0.85,0.85,0.83]) back_plate();
    color([0.85,0.85,0.83]) translate([0,0,-phone_t - felt_c - jaw_t - ex]) jaw();
    color([0.22,0.22,0.24]) for (sx=[-1,1]) translate([sx*post_dx, y_post, tp + ex]) knob();
    translate([0,0,ring_h - sp_h + ex]) {
        color([0.92,0.92,0.90]) base();
        color([0.3,0.5,0.9]) translate([ex*1.2,0,z_c]) cassette();
        along_axis(s_f + ex) {
            color([0.92,0.92,0.90]) tube();
            // lente e O-ring (non stampati)
            color([0.6,0.8,1.0,0.6]) translate([0,0,-ex/2]) lens_solid();
            color([0.1,0.1,0.1]) translate([0,0,t_top - 5.5 + groove_w/2]) rotate_extrude() translate([groove_root_r + or_cs/2,0]) circle(d=or_cs, $fn=16);
            translate([0,0,t_slit + c_slit + ex]) mirror([0,0,1]) {
                color([0.92,0.92,0.90]) cap();
                color([0.75,0.75,0.77]) translate([0,0,-ex/2]) slit_plate();
                // lame
                color([0.55,0.57,0.6]) for (sy=[-1,1]) translate([-blade_w/2, sy > 0 ? 0.025 : -blade_h - 0.025, clamp_t - ex/4]) cube([blade_w, blade_h, blade_t]);
            }
        }
    }
}

// lastra di stampa con tutti i pezzi
module plate_all() {
    translate([0, 0, 0]) base();
    translate([62, 0, t_top]) mirror([0,0,1]) tube();
    translate([62, 40, cap_len]) mirror([0,0,1]) cap();
    translate([30, 40, 0]) slit_plate();
    translate([-10, 45, 0]) cassette();
    translate([0, -70, 0]) back_plate();
    translate([0, -115, 0]) jaw();
    for (i=[0:1]) translate([75 + i*14, -40, 6]) mirror([0,0,1]) knob();
}

if (part == "assembly")   assembly();
if (part == "exploded")   assembly(ex = 18);
if (part == "section")    difference() { assembly(); translate([0,-200,-100]) cube(400); }
if (part == "base")       base();
if (part == "tube")       translate([0,0,t_top]) mirror([0,0,1]) tube();
if (part == "cap")        translate([0,0,cap_len]) mirror([0,0,1]) cap();
if (part == "slit_plate") slit_plate();
if (part == "cassette")   cassette();
if (part == "back_plate") back_plate();
if (part == "jaw")        jaw();
if (part == "knob")       translate([0,0,6]) mirror([0,0,1]) knob();
if (part == "plate_all")  plate_all();
