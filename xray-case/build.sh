#!/bin/sh
# Rigenera STL, sagome del piombo e immagini. Richiede openscad (e xvfb-run per i PNG).
set -e
cd "$(dirname "$0")"
SCAD=xray_case_2x2a.scad
ECHO=$(mktemp --suffix=.echo); openscad -o "$ECHO" $SCAD 2>/dev/null
N=$(sed -n 's/.*Piombo: \([0-9]*\) fogli.*/\1/p' "$ECHO"); cat "$ECHO"; rm -f "$ECHO"
rm -rf stl lead_templates && mkdir -p stl lead_templates render
for p in cup sleeve lid plinth tray lv_chimney hv_bushing window_frame shutter; do
  openscad -q -D "part=\"$p\"" -o stl/$p.stl $SCAD
done
i=0
while [ $i -lt "$N" ]; do
  for ext in svg dxf; do
    openscad -q -D 'part="lead_wall"' -D "layer=$i" -o lead_templates/wall_L$((i+1)).$ext $SCAD
  done
  i=$((i+1))
done
for p in lead_floor lead_lid lead_chimney_hv lead_chimney_lv lead_shutter; do
  for ext in svg dxf; do openscad -q -D "part=\"$p\"" -o lead_templates/${p#lead_}.$ext $SCAD; done
done
if command -v xvfb-run >/dev/null; then
  R="xvfb-run -a openscad -q --colorscheme=Tomorrow"
  $R -o render/assembly.png --imgsize=1100,1300 --camera=0,0,110,62,0,35,760 $SCAD
  $R -o render/assembly_rear.png --imgsize=1100,1300 --camera=0,0,110,62,0,215,760 $SCAD
  $R -o render/cup.png -D 'part="cup"' --imgsize=900,1000 --camera=0,0,100,62,0,340,560 $SCAD
  $R -o render/plinth.png -D 'part="plinth"' --imgsize=1000,800 --camera=0,0,25,55,0,200,420 $SCAD
  $R -o render/window_frame.png -D 'part="window_frame"' --imgsize=800,800 --camera=0,0,15,60,0,200,260 $SCAD
  $R -o render/hv_bushing.png -D 'part="hv_bushing"' --imgsize=700,800 --camera=0,0,35,70,0,30,230 $SCAD
fi
