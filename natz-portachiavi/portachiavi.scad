// Portachiavi "montagna" per Natz — versione stampa 3D (FDM)
// Sagoma e 3 canalature ricalcate dalla foto di riferimento, 4 nut colorati.
// Il nut si appoggia nella parte larga della canalatura e si tira giù:
// si incastra dove la canalatura si stringe, come un nut vero in fessura.
//
// Esporta gli STL con:
//   openscad -D 'parte="base"' -o stl/base.stl portachiavi.scad
//   openscad -D 'parte="nut"'  -o stl/nut.stl  portachiavi.scad
// oppure apri il file in OpenSCAD, scegli "parte" nel Customizer, F6, F7.

/* [Cosa generare] */
parte = "tutto"; // [tutto, base, nut, nut_x4, prova]

/* [Base] */
spessore_retro = 3;       // fondo pieno dietro le canalature (mm)
profondita = 12;          // profondità delle canalature (mm)
raggio_pianta = 1.5;      // arrotonda gli spigoli in pianta (vette, angoli delle canalature)
raccordo_bordo = 2.5;     // raccordo dello spigolo frontale esterno
raccordo_canalature = 1;  // raccordo del labbro delle canalature
smusso_retro = 0.6;       // piccolo smusso sul retro (evita il "piede d'elefante")
passo_raccordo = 0.3;     // altezza dei gradini del raccordo (≈ altezza layer)

/* [Nut] */
nut_largh_alto = 12;
nut_largh_basso = 7.2;
nut_altezza = 17.5;
nut_spess_alto = 8.5;     // deve stare < profondita
nut_spess_basso = 6.5;
nut_raggio = 1;           // arrotondamento spigoli
cavo_foro = 2.4;          // cavetto acciaio Ø1.5 o cordino Ø2
sede_nodo = 5;            // Ø della sede in cima per il nodo / la ghiera
sede_prof = 3;

/* [Fissaggio a muro] */
asola_foro = 8;     // Ø testa vite
asola_gambo = 4;    // Ø gambo vite
asola_corsa = 6;
tasca_vite = 12;    // spazio per la testa dentro il corpo
tasca_prof = 3.5;

/* [Hidden] */
$fn = 32;
H = spessore_retro + profondita;
asole = [[31.6,54.4],[104.4,54.4]];
// posizione dei nut nell'anteprima: [x, y in cima, rotazione, colore]
nut_foto = [[26.7,13.6,0,"Gold"],[62.6,41.3,0,"Crimson"],
            [100.2,21.4,0,"SeaGreen"],[122.9,39.9,18,"DeepSkyBlue"]];

// ricalcate dalla foto: sagoma e 3 canalature (mm, y=0 alla base)
sagoma = [[170.0,2.4],[160.6,26.1],[158.8,35.2],[139.3,89.8],[136.4,92.6],[133.1,92.8],[126.6,84.3],[121.7,84.3],[107.7,119.3],[105.7,119.3],[102.8,116.0],[97.9,116.0],[96.9,117.1],[92.0,137.8],[90.2,140.3],[88.0,140.3],[66.0,92.6],[59.2,81.0],[54.4,81.0],[40.7,104.6],[39.9,105.5],[36.9,104.6],[3.3,12.2],[0.0,0.2],[170.0,0.2]];

canalature = [
  [[32.0,46.2],[29.1,45.0],[30.5,32.4],[18.7,11.6],[19.7,-3.9],[29.3,-3.9],[30.7,8.1],[41.7,28.1],[41.1,31.8]],
  [[84.7,105.7],[82.0,104.9],[74.3,88.6],[77.6,70.4],[66.0,54.0],[65.8,51.1],[62.5,51.5],[62.3,53.1],[47.0,68.6],[42.1,78.4],[40.1,78.6],[38.9,77.0],[39.3,65.8],[54.6,39.7],[56.6,39.3],[56.6,35.8],[59.0,32.2],[59.7,15.1],[51.3,2.2],[51.3,-3.9],[78.0,-3.9],[78.0,2.2],[70.2,23.6],[68.4,34.8],[70.2,35.6],[79.4,46.6],[82.3,45.6],[90.8,29.3],[90.8,20.2],[95.3,11.2],[95.1,7.9],[92.0,2.0],[92.0,-3.9],[106.3,-3.9],[105.3,9.6],[107.3,18.9],[106.7,30.3],[94.9,44.0],[93.2,50.1],[92.2,50.7],[91.6,56.6],[84.3,84.3],[86.1,104.2]],
  [[131.3,72.3],[117.5,54.4],[112.2,38.1],[126.6,17.3],[126.6,14.5],[122.0,2.2],[122.0,-3.9],[143.3,-3.9],[143.3,2.6],[141.1,11.8],[131.7,20.4],[130.9,33.8],[125.6,46.8],[126.4,51.3],[129.3,51.5],[136.8,45.4],[147.4,21.8],[150.9,21.4],[150.9,27.7],[152.3,28.3],[152.5,30.9],[156.0,31.4],[156.0,33.2],[149.0,37.9],[135.2,65.4],[134.4,71.5]]
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

module nut_x4() for (i=[0:3]) translate([i*16,0,0]) nut();

if (parte == "base") base();
else if (parte == "nut") nut();
else if (parte == "nut_x4") nut_x4();
// pezzetto di base attorno alla strettoia del nut rosso: per provare l'incastro
else if (parte == "prova") intersection() { base(); translate([48,14,-1]) cube([30,36,H+2]); }
else {
  color("BurlyWood") base();
  color("SaddleBrown") linear_extrude(spessore_retro + 0.05) offset(delta=-0.3) sagoma2d();  // fondo scuro come l'originale
  for (n = nut_foto) color(n[3])
    translate([n[0], n[1], spessore_retro + nut_spess_alto/2 + 0.5])
      rotate(n[2]) translate([0, -nut_altezza, 0]) rotate([-90,0,0]) nut();
}
