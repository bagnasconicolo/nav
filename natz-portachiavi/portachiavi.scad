// Portachiavi "montagna" per Natz — versione stampa 3D (FDM)
// Base in legno-PLA con fessure "da arrampicata" + 4 nut colorati.
// Il nut entra dal basso nella fessura, sale e si incastra nella strettoia,
// esattamente come un nut vero in una fessura di roccia.
//
// Esporta gli STL con:
//   openscad -D 'parte="base"' -o stl/base.stl portachiavi.scad
//   openscad -D 'parte="nut"'  -o stl/nut.stl  portachiavi.scad
// oppure apri il file in OpenSCAD, scegli "parte" nel Customizer, F6, F7.

/* [Cosa generare] */
parte = "tutto"; // [tutto, base, nut, nut_x4]

/* [Base] */
spessore_retro = 3;     // fondo pieno dietro le fessure (mm)
profondita_fessure = 14; // spessore del corpo con le fessure (mm)
incisione = 0.8;        // profondità scritta
testo = "NATZ";
testo_h = 11;
testo_font = "Liberation Sans:style=Bold";

/* [Nut] */
nut_largh_alto = 16;
nut_largh_basso = 11;
nut_altezza = 18;
nut_spess_alto = 10;    // deve stare < profondita_fessure
nut_spess_basso = 8;
cavo_foro = 2.2;        // per cavetto acciaio Ø1.5 (o cordino Ø2)
cavo_interasse = 6;

/* [Fessure] */
ingresso = 19;   // dove passa il nut  (> nut_largh_alto)
strettoia = 13;  // dove si incastra   (< nut_largh_alto)

/* [Fissaggio a muro] */
asola_foro = 9;     // Ø testa vite
asola_gambo = 4.5;  // Ø gambo vite
asola_corsa = 10;
tasca_vite = 14;    // spazio per la testa dentro il corpo
tasca_prof = 4;

/* [Hidden] */
$fn = 48;
base_y = 185;
L = 220;

// Sagoma (y verso il basso come nel disegno, poi specchiata)
sagoma = [[0,base_y],[48,48],[68,82],[115,2],[133,34],[138,29],
          [165,74],[180,64],[L,base_y]];

// Fessure: punti dal basso verso l'alto + larghezza a ogni punto
fessure = [
  [[[34,195],[34,165],[42,140],[50,118],[46,100]],          [ingresso,ingresso,strettoia,9,7]],
  [[[80,195],[80,160],[86,130],[96,110],[102,88],[108,68]], [ingresso,ingresso,strettoia,9,8,6]],
  [[[125,195],[125,165],[121,140],[126,118],[122,100]],     [ingresso,ingresso,strettoia,9,7]],
  [[[170,195],[170,160],[164,132],[172,112],[176,96]],      [ingresso,ingresso,strettoia,9,7]],
  // rami decorativi, troppo stretti per il nut
  [[[96,110],[86,94],[88,84]],    [7,6,5]],
  [[[126,118],[138,104],[140,92]],[7,6,5]],
];
asole = [[60,150],[147,150]];
testo_pos = [118,50];

module fessura(p, w)
  for (i = [0:len(p)-2])
    hull() { translate(p[i]) circle(d=w[i]); translate(p[i+1]) circle(d=w[i+1]); }

// tutto il 2D viene disegnato con y verso il basso e poi ribaltato
module flip() mirror([0,1]) translate([0,-base_y]) children();

module base() {
  difference() {
    linear_extrude(spessore_retro + profondita_fessure) flip() polygon(sagoma);
    // fessure (cieche: il retro resta pieno)
    translate([0,0,spessore_retro]) linear_extrude(profondita_fessure + 1)
      flip() for (f = fessure) fessura(f[0], f[1]);
    // scritta incisa sul fronte
    translate([0,0,spessore_retro + profondita_fessure - incisione])
      linear_extrude(incisione + 1) flip()
        translate(testo_pos) mirror([0,1])
          text(testo, size=testo_h*0.72, font=testo_font, halign="center", spacing=1.1);
    // asole a buco di serratura nel retro + tasca per la testa della vite
    for (a = asole) translate([a[0], base_y - a[1], 0]) {
      // la testa della vite entra nel foro grande, poi il portachiavi scende e la vite resta nell'asola
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

// Nut: tronco di piramide, stampato in piedi (lato stretto sul piatto)
module nut() {
  a = nut_largh_alto/2; b = nut_largh_basso/2;
  c = nut_spess_alto/2; d = nut_spess_basso/2;
  difference() {
    hull() {
      translate([0,0,0.5]) cube([2*b, 2*d, 1], center=true);
      translate([0,0,nut_altezza-0.5]) cube([2*a, 2*c, 1], center=true);
    }
    // due fori per il cavo + canalina in cima, come un nut vero
    for (s = [-1,1]) translate([s*cavo_interasse/2,0,-1]) cylinder(d=cavo_foro, h=nut_altezza+2);
    translate([0,0,nut_altezza]) cube([cavo_interasse+cavo_foro, cavo_foro, 2*1.2], center=true);
  }
}

module nut_x4() for (i=[0:3]) translate([i*22,0,0]) nut();

if (parte == "base") base();
else if (parte == "nut") nut();
else if (parte == "nut_x4") nut_x4();
else {
  color("BurlyWood") base();
  // anteprima: i nut fermi nelle strettoie (punto dove la fessura è larga ~16.5)
  colori = ["Gold","Crimson","SeaGreen","DeepSkyBlue"];
  stop = [[37.3,154.6],[82.5,147.5],[123.3,154.6],[167.5,148.3]];
  for (i=[0:3]) color(colori[i])
    translate([stop[i][0], base_y-stop[i][1]-nut_altezza, spessore_retro + nut_spess_alto/2 + 0.5])
      rotate([-90,0,0]) nut();
}
