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
raggio_bordo = 1.5;       // arrotondamento dei bordi sul davanti (contorno e canalature)

/* [Nut] */
nut_altezza = 13.4;       // il profilo della foto viene scalato a questa altezza
nut_spessore = 5;         // piastrina: deve stare < profondita
nut_raggio = 0.6;         // arrotondamento degli spigoli
cavo_foro = 2;            // cavetto acciaio Ø1.5 (o cordino Ø1.5)

/* [Fissaggio a muro] */
asola_foro = 7;     // Ø testa vite
asola_gambo = 3.5;  // Ø gambo vite
asola_corsa = 5;
tasca_vite = 9;     // spazio per la testa dentro il corpo
tasca_prof = 3;

/* [Hidden] */
$fn = 32;
H = spessore_retro + profondita;
asole = [[24.1,41.6],[77,41.6]];
// posizione dei nut nell'anteprima: [x, y in cima, rotazione, colore]
nut_foto = [[20.4,10.4,0,"Gold"],[47.9,31.6,0,"Crimson"],[76.6,16.4,0,"SeaGreen"]];

// Profilo dei nut della foto (lato sinistro concavo, due scalini a destra),
// in unità della foto: alto 86.
nut_profilo = [[-15,0],[15,0],[17,4],[22,20],[21,25],[24,30],[24,36],[28,44],
               [30,56],[30,78],[27,84],[20,86],[-22,86],[-29,84],[-31,76],
               [-27,60],[-21,36],[-19,8],[-17,2]];

// ricalcate dalla foto: sagoma e canalature (tolta quella del nut blu) (mm, y=0 alla base)
// versanti spezzati: spalle e un piccolo gobbo sotto la vetta, come nella foto
sagoma = [[96,0],[91.5,28],[85.5,46],[82.5,64],[81,70],[78.5,68.8],[77.2,70.3],[70.4,105.4],[69.0,107.3],[67.3,107.3],[50.4,70.8],[45.3,62.0],[41.6,62.0],[31.1,80.0],[30.5,80.6],[28.2,80.0],[15,44],[9.5,24],[0,0]];

canalature = [
  [[24.4,35.3],[22.3,34.4],[23.4,24.8],[14.3,8.9],[15.1,-3.0],[22.4,-3.0],[23.5,6.2],[31.9,21.5],[31.4,24.3]],
  [[64.8,80.8],[62.7,80.2],[56.8,67.7],[59.3,53.9],[50.4,41.3],[50.3,39.1],[47.8,39.4],[47.6,40.6],[36.0,52.5],[32.2,59.9],[30.7,60.1],[29.7,58.9],[30.0,50.3],[41.7,30.4],[43.3,30.0],[43.3,27.4],[45.1,24.6],[45.6,11.5],[39.2,1.7],[39.2,-3.0],[59.6,-3.0],[59.6,1.7],[53.7,18.1],[52.3,26.6],[53.7,27.2],[60.7,35.7],[62.9,34.9],[69.4,22.4],[69.4,15.4],[72.9,8.6],[72.7,6.1],[70.4,1.6],[70.4,-3.0],[81.3,-3.0],[80.5,7.3],[82.0,14.5],[81.6,23.2],[72.6,33.6],[71.3,38.3],[70.5,38.8],[70.1,43.3],[64.5,64.5],[65.9,79.7]]
];

// ------------------------------------------------------------------ 2D
module liscia(r) offset(r=r) offset(delta=-r) offset(r=-r) offset(delta=r) children();

module sagoma2d()     liscia(raggio_pianta) polygon(sagoma);
module canalature2d() liscia(raggio_pianta) for (c = canalature) polygon(c);

module corpo2d()
  offset(r=raggio_pianta) offset(delta=-raggio_pianta)    // arrotonda i labbri all'imbocco
    difference() { sagoma2d(); canalature2d(); }

// ------------------------------------------------------------------ 3D
// arrotondamento vero (minkowski con una sfera): tutto il bordo davanti,
// contorno e labbri delle canalature, raggio raggio_bordo
module corpo3d() {
  r = raggio_bordo;
  intersection() {
    translate([0,0,-r]) minkowski() {
      linear_extrude(H) offset(delta=-r) corpo2d();
      sphere(r=r, $fn=24);
    }
    translate([-50,-50,0]) cube([300,300,H]);
  }
}

module base() {
  difference() {
    union() {
      // fondo (lato del piatto: spigolo vivo, appoggia meglio)
      linear_extrude(spessore_retro + 0.01) offset(r=raggio_bordo) offset(delta=-raggio_bordo) sagoma2d();
      // corpo con le canalature, con i bordi del davanti arrotondati
      corpo3d();
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

// Nut: piastrina col profilo della foto. Si stampa in piedi, lato stretto sul
// piatto. Il cavo entra dal basso nel foro centrale e si ferma in cima con una
// ghiera da crimpare.
module nut2d() scale(nut_altezza/86) polygon(nut_profilo);

module nut() {
  r = nut_raggio;
  difference() {
    rotate([90,0,0])
      minkowski() {
        linear_extrude(nut_spessore - 2*r, center=true) offset(delta=-r) nut2d();
        sphere(r=r, $fn=12);
      }
    translate([0,0,-1]) cylinder(d=cavo_foro, h=nut_altezza+2, $fn=20);
    translate([0,0,-5]) cube(10, center=true);   // piede piatto sul piatto di stampa
  }
}

module nut_x3() for (i=[0:2]) translate([i*14,0,0]) nut();

if (parte == "base") base();
else if (parte == "nut") nut();
else if (parte == "nut_x3") nut_x3();
// pezzetto di base attorno alla strettoia del nut rosso: per provare l'incastro
else if (parte == "prova") intersection() { base(); translate([36.7,10.7,-1]) cube([23,28,H+2]); }
else {
  color("BurlyWood") base();
  color("SaddleBrown") linear_extrude(spessore_retro + 0.05) offset(delta=-0.3) sagoma2d();  // fondo scuro come l'originale
  for (n = nut_foto) color(n[3])
    translate([n[0], n[1], spessore_retro + nut_spessore/2 + 0.3])
      rotate(n[2]) translate([0, -nut_altezza, 0]) rotate([-90,0,0]) nut();
}
