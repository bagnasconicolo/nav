# Modelli delle schede dei moduli

Questi file vengono da glacier-elettronica (`hardware/moduli`, ramo `claude/gallant-feynman-h18ciy`).

| File | Da dove | Come |
|---|---|---|
| `scheda_acquisizione.glb`, `modulo_meteo.glb` | `*/<nome>.step` (STEP di KiCad, con i colori) | `hardware/render3d/moduli/step2glb.py` (OCP / cadquery-ocp) |
| `acq_top.png`, `met_top.png` | Gerber F_Cu, F_Mask, F_Silkscreen, Edge_Cuts | `tools/texture_gerber.py` (gerbonara + cairosvg), maschera nera, 20 px/mm |

Allo stesso modo, `scheda3ch/bottom_nero.png` e `scheda3ch/holes.json` vengono dai Gerber B_* e da
PTH.drl della scheda a 3 canali. `scene.json` e `top_nero.png` sono copiati da
`hardware/render3d/out/3ch`.
