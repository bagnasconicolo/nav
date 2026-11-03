// Portachiavi "montagna" per Natz — versione stampa 3D (FDM)
// Sagoma e canalature ricalcate dalla foto di riferimento, 3 nut colorati.
// Il nut si appoggia nella parte larga della canalatura e si tira giù:
// si incastra dove la canalatura si stringe, come un nut vero in fessura.
//
// Esporta gli STL con:
//   openscad -D 'parte="base"' -o stl/base.stl portachiavi.scad
//   openscad -D 'parte="nut"'  -o stl/nut.stl  portachiavi.scad
// oppure apri il file in OpenSCAD, scegli "parte" nel Customizer, F6, F7.

/* [Cosa generare] */
parte = "tutto"; // [tutto, base, nut, nut_x3, prova]

/* [Base] */
spessore_retro = 3;       // fondo pieno dietro le canalature (mm)
profondita = 10;          // profondità delle canalature (mm)
raggio_pianta = 1.2;      // arrotonda gli spigoli in pianta (vette, angoli delle canalature)
raccordo_bordo = 2;       // raccordo dello spigolo frontale esterno
raccordo_canalature = 0.8;  // raccordo del labbro delle canalature
smusso_retro = 0.6;       // piccolo smusso sul retro (evita il "piede d'elefante")
passo_raccordo = 0.3;     // altezza dei gradini del raccordo (≈ altezza layer)

/* [Nut] */
nut_largh_alto = 9.2;
nut_largh_basso = 5.5;
nut_altezza = 13.4;
nut_spess_alto = 7;       // deve stare < profondita
nut_spess_basso = 5.5;
nut_raggio = 0.8;          // arrotondamento spigoli
cavo_foro = 2.1;          // cavetto acciaio Ø1.5 o cordino Ø2
sede_nodo = 4;            // Ø della sede in cima per il nodo / la ghiera
sede_prof = 2.5;

/* [Fissaggio a muro] */
asola_foro = 7;     // Ø testa vite
asola_gambo = 3.5;   // Ø gambo vite
asola_corsa = 5;
tasca_vite = 10;    // spazio per la testa dentro il corpo
tasca_prof = 3;

/* [Hidden] */
$fn = 32;
H = spessore_retro + profondita;
asole = [[24.1,41.6],[79.9,41.6]];
// posizione dei nut nell'anteprima: [x, y in cima, rotazione, colore]
nut_foto = [[20.4,10.4,0,"Gold"],[47.9,31.6,0,"Crimson"],
            [76.6,16.4,0,"SeaGreen"]];

// ricalcate dalla foto: sagoma e canalature (tolta quella del nut blu) (mm, y=0 alla base)
// tolto il picco di destra insieme alla canalatura del nut blu
sagoma = [[114.0,0.0],[96.8,64.5],[93.1,64.5],[82.4,91.2],[80.8,91.2],[78.6,88.7],[74.9,88.7],[74.1,89.5],[70.4,105.4],[69.0,107.3],[67.3,107.3],[50.4,70.8],[45.3,62.0],[41.6,62.0],[31.1,80.0],[30.5,80.6],[28.2,80.0],[2.5,9.3],[0.0,0.2]];

canalature = [
  [[24.4,35.3],[22.3,34.4],[23.4,24.8],[14.3,8.9],[15.1,-3.0],[22.4,-3.0],[23.5,6.2],[31.9,21.5],[31.4,24.3]],
  [[64.8,80.8],[62.7,80.2],[56.8,67.7],[59.3,53.9],[50.4,41.3],[50.3,39.1],[47.8,39.4],[47.6,40.6],[36.0,52.5],[32.2,59.9],[30.7,60.1],[29.7,58.9],[30.0,50.3],[41.7,30.4],[43.3,30.0],[43.3,27.4],[45.1,24.6],[45.6,11.5],[39.2,1.7],[39.2,-3.0],[59.6,-3.0],[59.6,1.7],[53.7,18.1],[52.3,26.6],[53.7,27.2],[60.7,35.7],[62.9,34.9],[69.4,22.4],[69.4,15.4],[72.9,8.6],[72.7,6.1],[70.4,1.6],[70.4,-3.0],[81.3,-3.0],[80.5,7.3],[82.0,14.5],[81.6,23.2],[72.6,33.6],[71.3,38.3],[70.5,38.8],[70.1,43.3],[64.5,64.5],[65.9,79.7]]
];

// ------------------------------------------------------------------ 2D
module liscia(r) offset(r=r) offset(delta=-r) offset(r=-r) offset(delta=r) children();

module sagoma2d()     liscia(raggio_pianta) polygon(sagoma);
module canalature2d() liscia(raggio_pianta) for (c = canalature) polygon(c);

// pianta del corpo con il bordo rientrato di d e le canalature allargate di c
module corpo2d(d=0, c=0)
  offset(r=raggio_pianta) offset(delta=-raggio_pianta)    // arrotonda i labbri all'imbocco
    difference() { offset(delta=-d) sagoma2d(); offset(r=c) canalature2d(); }

function quarto(R, z) = R - sqrt(max(0, R*R - z*z));   // profilo del raccordo

// ------------------------------------------------------------------ 3D
module base() {
  Rb = raccordo_bordo; Rc = raccordo_canalature;
  zr = H - Rb;                                // inizio del raccordo frontale
  n = ceil(Rb / passo_raccordo);
  difference() {
    union() {
      linear_extrude(smusso_retro) offset(delta=-smusso_retro) sagoma2d();
      translate([0,0,smusso_retro]) linear_extrude(spessore_retro - smusso_retro + 0.01) sagoma2d();
      translate([0,0,spessore_retro]) linear_extrude(zr - spessore_retro + 0.01) corpo2d();
      // raccordo frontale a gradini (invisibili a layer 0.2-0.3)
      for (i = [0:n-1]) {
        z = (i + 1) * passo_raccordo;
        translate([0,0,zr + i*passo_raccordo]) linear_extrude(passo_raccordo + 0.01)
          corpo2d(quarto(Rb, z), quarto(Rc, max(0, z - (Rb - Rc))));
      }
    }
    // asole a buco di serratura nel retro + tasca per la testa della vite:
    // la testa entra nel foro grande, poi il portachiavi scende e la vite resta nell'asola
    for (a = asole) translate(a) {
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
// (lato stretto sul piatto). Il cavo passa nel foro centrale e si ferma
// con un nodo o una ghiera nella sede in cima.
module nut() {
  r = nut_raggio;
  a = nut_largh_alto/2 - r;  b = nut_largh_basso/2 - r;
  c = nut_spess_alto/2 - r;  d = nut_spess_basso/2 - r;
  difference() {
    hull() {
      linear_extrude(0.01) offset(r=r) square([2*b, 2*d], center=true);
      for (sx=[-1,1], sy=[-1,1]) translate([sx*a, sy*c, nut_altezza - r]) sphere(r=r);
    }
    translate([0,0,-1]) cylinder(d=cavo_foro, h=nut_altezza+2);
    translate([0,0,nut_altezza - sede_prof]) cylinder(d=sede_nodo, h=sede_prof+1);
    translate([0,0,-0.01]) cylinder(d1=cavo_foro+1, d2=cavo_foro, h=0.5);
  }
}

module nut_x3() for (i=[0:2]) translate([i*13,0,0]) nut();

if (parte == "base") base();
else if (parte == "nut") nut();
else if (parte == "nut_x3") nut_x3();
// pezzetto di base attorno alla strettoia del nut rosso: per provare l'incastro
else if (parte == "prova") intersection() { base(); translate([36.7,10.7,-1]) cube([23,28,H+2]); }
else {
  color("BurlyWood") base();
  color("SaddleBrown") linear_extrude(spessore_retro + 0.05) offset(delta=-0.3) sagoma2d();  // fondo scuro come l'originale
  for (n = nut_foto) color(n[3])
    translate([n[0], n[1], spessore_retro + nut_spess_alto/2 + 0.5])
      rotate(n[2]) translate([0, -nut_altezza, 0]) rotate([-90,0,0]) nut();
}
