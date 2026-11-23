// Scatoline aperte (senza coperchio) per minerali - parametrico
// Materiale: PETG-CF  |  Unità: mm
// Le misure esterne seguono una griglia di 25 mm (meno il gioco) così
// scatole di formati diversi si affiancano senza spazi in un cassetto.

/* [Formato] */
celle_x   = 2;     // numero di celle da 25 mm in X
celle_y   = 2;     // numero di celle da 25 mm in Y
altezza   = 22;    // altezza esterna totale
griglia   = 25;    // passo della griglia
gioco     = 0.5;   // gioco totale tra scatole affiancate

/* [Pareti] */
parete    = 1.8;   // spessore parete (≈3 linee con ugello 0.6)
fondo     = 1.6;   // spessore fondo
r_est     = 3;     // raggio angoli esterni (verticali)
raccordo  = 2;     // smusso 45° interno fondo/parete (facilita la presa)
smusso_base = 0.6; // smusso esterno sul bordo inferiore (anti elephant-foot)

/* [Etichetta] */
etichetta = true;  // incavo frontale per etichetta adesiva
etich_h   = 8;     // altezza incavo
etich_prof= 0.4;   // profondità incavo

$fn = 48;

L = celle_x*griglia - gioco;
W = celle_y*griglia - gioco;

module rrect(l, w, r, h) {
  r2 = max(min(r, l/2-0.01, w/2-0.01), 0.01);
  linear_extrude(h) offset(r=r2) square([l-2*r2, w-2*r2], center=true);
}

module esterno() {
  hull() {
    rrect(L-2*smusso_base, W-2*smusso_base, r_est-smusso_base, 0.01);
    translate([0,0,smusso_base]) rrect(L, W, r_est, altezza-smusso_base);
  }
}

module cavita() {
  li = L-2*parete; wi = W-2*parete; ri = max(r_est-parete, 0.5);
  hull() {
    translate([0,0,fondo]) rrect(li-2*raccordo, wi-2*raccordo, max(ri-raccordo,0.5), 0.01);
    translate([0,0,fondo+raccordo]) rrect(li, wi, ri, altezza);
  }
}

module incavo_etichetta() {
  lw = L - 2*r_est - 2;
  translate([-lw/2, -W/2-1, (altezza-etich_h)/2])
    cube([lw, 1+etich_prof, etich_h]);
}

difference() {
  esterno();
  cavita();
  if (etichetta && altezza >= etich_h + 6) incavo_etichetta();
}
