"""Schema in sezione (piano x=0) del case 2X2A, stessi parametri di default dello .scad.
Uso: python3 tools/section_svg.py > render/section.svg"""
import math

tube_d, tube_seated_h, anode_rim_h = 38, 120, 55
socket_h, tray_h, hv_clear = 15, 20, 50
lead_n, plinth_h = 3, 50
lead_t, lead_tol, wall_in, wall_out = 3.0, 0.6, 2.4, 2.4
floor_t, chan_floor, feet_h = 3, 1.2, 5
window_d, membrane_t, boss_h = 20, 0.8, 6

cav = math.ceil(tube_d + 2*hv_clear)
cav_h = lead_t + tray_h + socket_h + tube_seated_h + hv_clear
H = floor_t + cav_h
hi = cav/2; c_in = hi + wall_in; c_out = c_in + lead_t + lead_tol; outer = c_out + wall_out
win_z = floor_t + lead_t + tray_h + socket_h + anode_rim_h
z_sock = floor_t + lead_t + tray_h
z_tube = z_sock + socket_h

S = 2.75                      # px per mm
W, Hpx = 1000, 900
ox, oz = 470, 700        # origine (y=0, z=0)
def X(y): return ox + y*S
def Z(z): return oz - z*S
out = []
def rect(y0, z0, y1, z1, fill, stroke="none", op=1, sw=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(f'<rect x="{X(min(y0,y1)):.1f}" y="{Z(max(z0,z1)):.1f}" width="{abs(y1-y0)*S:.1f}" '
               f'height="{abs(z1-z0)*S:.1f}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}"{d}/>')
def line(y0, z0, y1, z1, c="#222", sw=1, dash=None, marker=False):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = ' marker-end="url(#a)"' if marker else ""
    out.append(f'<line x1="{X(y0):.1f}" y1="{Z(z0):.1f}" x2="{X(y1):.1f}" y2="{Z(z1):.1f}" stroke="{c}" stroke-width="{sw}"{d}{m}/>')
def text(y, z, s, size=13, anchor="start", c="#111", bold=False):
    b = ' font-weight="bold"' if bold else ""
    out.append(f'<text x="{X(y):.1f}" y="{Z(z):.1f}" font-size="{size}" text-anchor="{anchor}" fill="{c}"{b}>{s}</text>')

PLA, PB = "#7fa7c9", "#4a4a4a"
# corpo: pareti stampate e piombo
for s in (-1, 1):
    rect(s*hi, floor_t, s*c_in, H, PLA)
    rect(s*c_out, 0, s*outer, H, PLA)
    for i in range(lead_n):
        rect(s*(c_in + lead_tol/2 + i), chan_floor, s*(c_in + lead_tol/2 + i + 1), H, PB if i % 2 == 0 else '#777')
rect(-outer, 0, outer, chan_floor, PLA); rect(-c_in, 0, c_in, floor_t, PLA)
for i in range(lead_n): rect(-(cav-0.5)/2, floor_t + i, (cav-0.5)/2, floor_t + i + 1, PB if i % 2 == 0 else '#777')
# basamento con connettori
po = outer + 3.3
rect(-po, -plinth_h, po, -plinth_h + 3, '#3d5a5a')
for s_ in (-1, 1): rect(s_*po, -plinth_h, s_*(outer - 5), 4, '#3d5a5a')
text(0, -plinth_h/2 + 2, 'basamento: connettori FIL/K · INTLK · GND · AUX sul retro', 11, 'middle', '#333')
# coperchio
for i in range(lead_n): rect(-outer, H + i, outer, H + i + 1, PB if i % 2 == 0 else '#777')
rect(-outer-2.8, H + lead_t, outer+2.8, H + lead_t + 3, PLA)
for s in (-1, 1): rect(s*(outer+0.4), H - 8, s*(outer+2.8), H + lead_t + 3, PLA)
# finestra: foro esterno, foro piombo, membrana
rect(-c_out-0.1, win_z - window_d/2 - 1, -outer-0.1, win_z + window_d/2 + 1, "white")
rect(-(c_in + lead_tol/2 + lead_t)-0.05, win_z - window_d/2, -(c_in + lead_tol/2)+0.05, win_z + window_d/2, "white")
rect(-hi, win_z - window_d/2 - 1, -hi - (wall_in - membrane_t), win_z + window_d/2 + 1, "white")
# modulo finestra (filtro Al + otturatore)
fy = -outer - boss_h
rect(fy, win_z - 27, fy - 3, win_z + 55, "#f0a030")
rect(fy - 3, win_z - 25, fy - 4.2, win_z + 40, "#c8c8d0")           # filtro Al
rect(fy - 4.2, win_z - 27, fy - 6.2, win_z + 55, "#f0a030")
rect(fy - 6.2, win_z - 25, fy - 12.2, win_z + 55, "#f0a030", op=0.35)
rect(fy - 7.8, win_z + 25, fy - 9.8, win_z + 55, PB)                 # piombo otturatore (sollevato = APERTO)
rect(fy - 12.2, win_z - 27, fy - 14.2, win_z + 55, "#f0a030")
for (a, b) in [(fy, fy-3), (fy-4.2, fy-6.2), (fy-12.2, fy-14.2)]:
    rect(a, win_z - window_d/2 - 1, b, win_z + window_d/2 + 1, "white")
# supporto, zoccolo, tubo
rect(-30, z_sock - 4, 30, z_sock, "#f0a030"); rect(-22, floor_t + lead_t, -14, z_sock - 4, "#f0a030")
rect(14, floor_t + lead_t, 22, z_sock - 4, "#f0a030")
rect(-16, z_sock, 16, z_tube, "#222")
r = tube_d/2 - 1
out.append(f'<path d="M{X(-r):.1f},{Z(z_tube):.1f} L{X(-r):.1f},{Z(z_tube+tube_seated_h-22):.1f} '
           f'Q{X(-r):.1f},{Z(z_tube+tube_seated_h-8):.1f} {X(0):.1f},{Z(z_tube+tube_seated_h-8):.1f} '
           f'Q{X(r):.1f},{Z(z_tube+tube_seated_h-8):.1f} {X(r):.1f},{Z(z_tube+tube_seated_h-22):.1f} '
           f'L{X(r):.1f},{Z(z_tube):.1f} Z" fill="#dff4f7" stroke="#6aa" stroke-width="1.2"/>')
rect(-8, z_tube + anode_rim_h, 8, z_tube + anode_rim_h + 30, "#b8b8b8", "#666")          # placca
line(0, z_tube + anode_rim_h - 3, 0, z_tube + anode_rim_h + 26, "#c60", 2)             # catodo
rect(-4.5, z_tube + tube_seated_h - 8, 4.5, z_tube + tube_seated_h, "#999", "#555")     # cappuccio
# emissione
ez = z_tube + anode_rim_h
for s in (-1, 1):
    out.append(f'<circle cx="{X(s*8):.1f}" cy="{Z(ez):.1f}" r="5" fill="#e33"/>')
for ang in (-35, -15, 0, 15, 35):
    a = math.radians(ang)
    line(-10, ez, -10 - 45*math.cos(a), ez + 45*math.sin(a), "#e33", 1.6, "5,3", marker=True)
    line(10, ez, 10 + 45*math.cos(a), ez + 45*math.sin(a), "#e33", 1.6, "5,3", marker=True)
line(-hi, win_z, fy - 40, win_z, "#e33", 3, marker=True)
# quote
line(8, ez - 6, hi, ez - 6, "#06c", 1, "3,2"); text(outer + 6, ez - 12, "≥ 50 mm aria AT → piombo", 11, c="#06c")
line(-30, H - hv_clear, -30, H, "#06c", 1, "3,2"); text(-28, H - 22, "≥ 50 mm", 11, c="#06c")
# etichette
text(-outer - 2, win_z - 40, "finestra Ø20 nel piombo", 11, "end")
text(-outer - 2, win_z - 53, "+ membrana stampata 0,8 mm", 11, "end")
text(fy - 7, win_z + 72, "filtro Al + otturatore Pb", 11, "middle")
text(fy - 7, win_z + 60, "(qui: aperto)", 11, "middle")
text(outer + 6, ez + 4, "anello di emissione:", 12, c="#c00", bold=True)
text(outer + 6, ez - 3, "bordo inferiore della placca", 11, c="#c00")
text(0, z_tube + tube_seated_h + 4, "cappuccio anodico (+AT)", 11, "middle")
text(0, z_sock - 14, "supporto + zoccolo UX4", 11, "middle")
text(0, H + 14, "coperchio: 3 fogli Pb 1 mm sotto, PETG sopra (+ passante AT)", 11, "middle")
text(outer + 6, H - 30, "parete: PETG 2,4 | 3 × Pb 1 mm | PETG 2,4", 11)
text(0, -plinth_h - 12, "fondo: PETG 3 + 3 × Pb 1 mm (il Pb delle pareti scende sotto quello del fondo)", 11, "middle")

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hpx}" viewBox="0 0 {W} {Hpx}" '
       f'font-family="Helvetica,Arial,sans-serif"><rect width="100%" height="100%" fill="white"/>'
       '<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
       '<path d="M0,0 L8,4 L0,8 Z" fill="#e33"/></marker></defs>'
       f'<text x="20" y="28" font-size="18" font-weight="bold">Case schermato 2X2A — sezione (quote in mm)</text>'
       + "".join(out) + "</svg>")
print(svg)
