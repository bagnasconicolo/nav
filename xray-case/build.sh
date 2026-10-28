#!/bin/sh
# Rigenera STL, sagome del piombo e immagini. Richiede openscad (e xvfb-run per i PNG).
set -e
cd "$(dirname "$0")"
SCAD=xray_case_2x2a.scad
ECHO=$(mktemp --suffix=.echo); openscad -o "$ECHO" $SCAD 2>/dev/null
N=$(sed -n 's/.*Piombo: \([0-9]*\) fogli.*/\1/p' "$ECHO"); cat "$ECHO"; rm -f "$ECHO"
rm -rf stl lead_templates && mkdir -p stl lead_templates render
for p in body lid plinth tray hood window_frame shutter hv_bushing; do
  openscad -q -D "part=\"$p\"" -o stl/$p.stl $SCAD
done
i=0
while [ $i -lt "$N" ]; do
  for f in front back side; do
    for ext in svg dxf; do
      openscad -q -D 'part="lead_wall"' -D "layer=$i" -D "face=\"$f\"" -o lead_templates/wall_L$((i+1))_$f.$ext $SCAD
    done
  done
  i=$((i+1))
done
for p in lead_floor lead_lid lead_shutter lead_hood_roof lead_hood_side; do
  for ext in svg dxf; do openscad -q -D "part=\"$p\"" -o lead_templates/${p#lead_}.$ext $SCAD; done
done
if command -v xvfb-run >/dev/null; then
  R="xvfb-run -a openscad -q --colorscheme=Tomorrow"
  $R -o render/assembly.png --imgsize=1200,1300 --camera=0,0,110,62,0,35,900 $SCAD
  $R -o render/assembly_rear.png --imgsize=1200,1300 --camera=0,0,110,62,0,215,900 $SCAD
  $R -o render/body.png -D 'part="body"' --imgsize=1000,1000 --camera=0,0,100,62,0,340,700 $SCAD
  $R -o render/plinth.png -D 'part="plinth"' --imgsize=1000,800 --camera=0,0,20,55,0,200,520 $SCAD
  $R -o render/window_frame.png -D 'part="window_frame"' --imgsize=800,800 --camera=0,0,15,60,0,200,260 $SCAD
  $R -o render/hood.png -D 'part="hood"' --imgsize=700,700 --camera=16,16,0,235,0,30,160 $SCAD
  $R -o render/hv_bushing.png -D 'part="hv_bushing"' --imgsize=700,700 --camera=0,0,30,70,0,30,200 $SCAD
fi
