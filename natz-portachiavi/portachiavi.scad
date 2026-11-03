// Portachiavi "montagna" per Natz — versione stampa 3D (FDM)
// Base a montagna con fessure "da arrampicata" + 3 nut colorati.
// Il nut entra dal basso nella fessura, sale e si incastra nella strettoia,
// esattamente come un nut vero in una fessura di roccia.
//
// Esporta gli STL con:
//   openscad -D 'parte="base"' -o stl/base.stl portachiavi.scad
//   openscad -D 'parte="nut"'  -o stl/nut.stl  portachiavi.scad
// oppure apri il file in OpenSCAD, scegli "parte" nel Customizer, F6, F7.

/* [Cosa generare] */
parte = "tutto"; // [tutto, base, nut, nut_x3]

/* [Base] */
spessore_retro = 3;       // fondo pieno dietro le fessure (mm)
profondita_fessure = 12;  // spessore del corpo con le fessure (mm)
raggio_punte = 2;       // arrotondamento delle vette, delle selle e degli spigoli in pianta
raccordo_bordo = 2.5;      // raccordo dello spigolo frontale esterno
raccordo_fessure = 1.2;   // raccordo del labbro delle fessure
smusso_retro = 0.6;       // piccolo smusso sul retro (evita il "piede d'elefante")
passo_raccordo = 0.3;     // altezza dei gradini del raccordo (≈ altezza layer)

/* [Nut] */
nut_largh_alto = 14;
nut_largh_basso = 10;
nut_altezza = 16;
nut_spess_alto = 9;        // deve stare < profondita_fessure
nut_spess_basso = 7;
nut_raggio = 1.2;         // arrotondamento spigoli del nut
cavo_foro = 2.2;          // per cavetto acciaio Ø1.5 (o cordino Ø2)
cavo_interasse = 5.5;

/* [Fessure] */
ingresso = 17;   // dove passa il nut  (> nut_largh_alto)
strettoia = 11.5;  // dove si incastra   (< nut_largh_alto)
bocca = 20;      // svasatura all'imbocco in basso

/* [Fissaggio a muro] */
asola_foro = 9;     // Ø testa vite
asola_gambo = 4.5;  // Ø gambo vite
asola_corsa = 8; 
tasca_vite = 14;    // spazio per la testa dentro il corpo
tasca_prof = 4;

/* [Hidden] */
$fn = 32;
base_y = 135;
L = 160;
H = spessore_retro + profondita_fessure;

// Sagoma (y verso il basso come nel disegno, poi ribaltata)
sagoma = [[0,base_y],[35,35],[49.5,60],[84,1.5],[97,25],[100,21],
          [120,54],[131,47],[L,base_y]];

// Fessure: [x, y, larghezza] dal basso verso l'alto.
// Tratto 1-3: canale dritto dove scorre il nut; 3-4: strettoia dove si
// incastra; poi la fessura sale a zig-zag e si chiude fino a un filo.
I = ingresso; S = strettoia; B = bocca;
fessure_nut = [
  [[36,147,B],[36,132,I],[38,117,I],[41,102,S],[43,94,8.5],[40,86,7],[43,79,5],[40,72,3.5],[41,66,1.4]],
  [[80,147,B],[80,132,I],[82,117,I],[85,102,S],[90,93,8.5],[88,84,7],[93,75,5.5],[91,67,4.5],[95,59,3.2],[94,52,2.2],[97,46,1.2]],
  [[122,147,B],[122,132,I],[120,117,I],[117,102,S],[120,94,8.5],[117,86,7],[121,78,5.5],[119,72,4],[123,67,2.8],[122,62,1.4]],
];
// diramazioni sottili (il nut non ci entra)
rami = [
  [[43,94,5],[49,89,4],[53,86,2.8],[55,81,1.4]],
  [[88,84,5],[82,77,4],[83,71,2.8],[79,66,1.4]],
  [[120,94,5],[126,89,4],[129,85,2.6],[132,82,1.4]],
];
asole = [[60,118],[137,118]];

// ------------------------------------------------------------------ 2D
module flip() mirror([0,1]) translate([0,-base_y]) children();

module tratto(p)   // segmento a larghezza variabile
  for (i = [0:len(p)-2])
    hull() { translate([p[i][0],p[i][1]]) circle(d=p[i][2]);
             translate([p[i+1][0],p[i+1][1]]) circle(d=p[i+1][2]); }

module fessure2d() flip() { for (f = fessure_nut) tratto(f); for (r = rami) tratto(r); }

module sagoma2d()   // vette e selle arrotondate
  offset(r=raggio_punte) offset(delta=-raggio_punte)
  offset(r=-raggio_punte) offset(delta=raggio_punte)
    flip() polygon(sagoma);

// pianta del corpo a una certa "rientranza" d (bordo) e allargamento c (fessure)
module corpo2d(d=0, c=0)
  offset(r=raggio_punte/2) offset(delta=-raggio_punte/2)   // arrotonda i labbri all'imbocco
    difference() { offset(delta=-d) sagoma2d(); offset(r=c) fessure2d(); }

function quarto(R, z) = R - sqrt(max(0, R*R - z*z));   // profilo del raccordo

// ------------------------------------------------------------------ 3D
module base() {
  Rb = raccordo_bordo; Rf = raccordo_fessure;
  zr = H - Rb;                                // inizio del raccordo frontale
  n = ceil(Rb / passo_raccordo);
  difference() {
    union() {
      // retro, con smusso sul lato del piatto
      linear_extrude(smusso_retro) offset(delta=-smusso_retro) sagoma2d();
      translate([0,0,smusso_retro]) linear_extrude(spessore_retro - smusso_retro + 0.01) sagoma2d();
      // corpo dritto con le fessure
      translate([0,0,spessore_retro]) linear_extrude(zr - spessore_retro + 0.01) corpo2d();
      // raccordo frontale a gradini (invisibili a layer 0.2-0.25)
      for (i = [0:n-1]) {
        z = i * passo_raccordo;
        translate([0,0,zr + z]) linear_extrude(passo_raccordo + 0.01)
          corpo2d(quarto(Rb, z + passo_raccordo),
                  quarto(Rf, max(0, z + passo_raccordo - (Rb - Rf))));
      }
    }
    // asole a buco di serratura nel retro + tasca per la testa della vite:
    // la testa entra nel foro grande, poi il portachiavi scende e la vite resta nell'asola
    for (a = asole) translate([a[0], base_y - a[1], 0]) {
      translate([0,0,-1]) linear_extrude(spessore_retro + 2) {
        circle(d=asola_foro);
        hull() { translate([0,2]) circle(d=asola_gambo);
                 translate([0,asola_corsa]) circle(d=asola_gambo); }
      }
      translate([0,0,spessore_retro]) linear_extrude(tasca_prof)
        hull() { circle(d=tasca_vite); translate([0,asola_corsa]) circle(d=tasca_vite); }
    }
  }
}

// Nut: tronco di piramide con spigoli arrotondati, stampato in piedi
// (lato stretto con i fori sul piatto)
module nut() {
  r = nut_raggio;
  a = nut_largh_alto/2 - r;  b = nut_largh_basso/2 - r;
  c = nut_spess_alto/2 - r;  d = nut_spess_basso/2 - r;
  difference() {
    hull() {
      linear_extrude(0.01) offset(r=r) square([2*b, 2*d], center=true);
      for (sx=[-1,1], sy=[-1,1]) translate([sx*a, sy*c, nut_altezza - r]) sphere(r=r);
    }
    // due fori per il cavo + canalina in cima, come un nut vero
    for (s = [-1,1]) translate([s*cavo_interasse/2,0,-1]) cylinder(d=cavo_foro, h=nut_altezza+2);
    translate([0,0,nut_altezza]) rotate([0,90,0])
      cylinder(d=cavo_foro*1.1, h=cavo_interasse, center=true);
    // smusso d'ingresso dei fori (aiuta il cavo e il primo layer)
    for (s = [-1,1]) translate([s*cavo_interasse/2,0,-0.01]) cylinder(d1=cavo_foro+1, d2=cavo_foro, h=0.5);
  }
}

module nut_x3() for (i=[0:2]) translate([i*20,0,0]) nut();

if (parte == "base") base();
else if (parte == "nut") nut();
else if (parte == "nut_x3") nut_x3();
else {
  color("BurlyWood") base();
  // anteprima: ogni nut fermo dove la fessura è larga quanto lui
  colori = ["Gold","Crimson","DeepSkyBlue"];
  t = (ingresso - nut_largh_alto - 0.5) / (ingresso - strettoia);
  for (i=[0:2]) {
    p = fessure_nut[i][2] + t * (fessure_nut[i][3] - fessure_nut[i][2]);
    color(colori[i])
      translate([p[0], base_y - p[1] - nut_altezza, spessore_retro + nut_spess_alto/2 + 0.5])
        rotate([-90,0,0]) nut();
  }
}
