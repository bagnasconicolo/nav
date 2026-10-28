"""Schema in sezione (piano x=0) del case cilindrico 2X2A, stessi parametri di default dello .scad.
I camini AT/BT non stanno nel piano di sezione: sono disegnati proiettati (tratteggio).
Uso: python3 tools/section_svg.py > render/section.svg"""
import math

tube_d, tube_seated_h, anode_rim_h, anode_r = 38, 120, 55, 9
socket_h, tray_h, hv_clear, top_clear = 15, 20 - 6, 35, 40
lead_n, lead_tol, wall_in, wall_out = 3, 1.0, 3.0, 2.0
floor_t, fl_t, plinth_h = 4, 2, 58
window_d, membrane_t, boss_h = 20, 0.8, 6
cable_d, hv_off, lv_off, hv_L, lv_L = 8, 40, 40, 50, 40

lead_t = lead_n * 1.0
cav_r = tube_d/2 + hv_clear
cup_or = cav_r + wall_in
sl_ir = cup_or + lead_t + lead_tol
sl_or = sl_ir + wall_out
cav_h = lead_t + tray_h + socket_h + tube_seated_h + top_clear
H = floor_t + cav_h
win_z = floor_t + lead_t + tray_h + socket_h + anode_rim_h
z_sock = floor_t + lead_t + tray_h
z_tube = z_sock + socket_h
R_pl = sl_or + 3.5
hv_y = hv_off * math.sin(math.radians(45))
lv_y = -lv_off * math.sin(math.radians(45))

S = 2.9
W, Hpx = 1000, 1000
ox, oz = 470, 770
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
def text(y, z, s, size=12, anchor="start", c="#111", bold=False):
    b = ' font-weight="bold"' if bold else ""
    out.append(f'<text x="{X(y):.1f}" y="{Z(z):.1f}" font-size="{size}" text-anchor="{anchor}" fill="{c}"{b}>{s}</text>')

PLA, PLA2, PB, PB2 = "#7fa7c9", "#a9c3da", "#4a4a4a", "#7a7a7a"
OR = "#f0a030"

# basamento
rect(-R_pl, -plinth_h, R_pl, -plinth_h + 3, "#3d5a5a")
for s in (-1, 1): rect(s*R_pl, -plinth_h, s*(sl_or - 5), 4, "#3d5a5a")
text(R_pl + 6, -plinth_h/2 + 6, "basamento con connettori", 11)
text(R_pl + 6, -plinth_h/2 - 7, "FIL/K · INTLK · GND · AUX (retro)", 11)
# bicchiere (parete isolante), flangia, fondo
for s in (-1, 1):
    rect(s*cav_r, floor_t, s*cup_or, H, PLA)
    rect(s*sl_ir, fl_t, s*sl_or, H, PLA2)
    for i in range(lead_n):
        r = cup_or + lead_tol/4 + i
        rect(s*r, fl_t, s*(r + 1), H, PB if i % 2 == 0 else PB2)
rect(-sl_or, 0, sl_or, fl_t, PLA); rect(-cup_or, 0, cup_or, floor_t, PLA)
for i in range(lead_n): rect(-(cav_r - 0.25), floor_t + i, cav_r - 0.25, floor_t + i + 1, PB if i % 2 == 0 else PB2)
# coperchio
for i in range(lead_n): rect(-sl_or, H + i, sl_or, H + i + 1, PB if i % 2 == 0 else PB2)
rect(-sl_or - 2.8, H + lead_t, sl_or + 2.8, H + lead_t + 3, PLA)
for s in (-1, 1): rect(s*(sl_or + 0.4), H - 8, s*(sl_or + 2.8), H + lead_t + 3, PLA)
# finestra
rect(-sl_ir + 0.1, win_z - window_d/2 - 1, -sl_or - 0.1, win_z + window_d/2 + 1, "white")
for i in range(lead_n):
    r = cup_or + lead_tol/4 + i
    rect(-r + 0.05, win_z - window_d/2, -r - 1.05, win_z + window_d/2, "white")
rect(-cav_r, win_z - window_d/2 - 1, -(cup_or - membrane_t), win_z + window_d/2 + 1, "white")
fy = -sl_or - boss_h
rect(fy, win_z - 27, fy - 3, win_z + 55, OR)
rect(fy - 3, win_z - 25, fy - 4.2, win_z + 40, "#c8c8d0")
rect(fy - 4.2, win_z - 27, fy - 6.2, win_z + 55, OR)
rect(fy - 6.2, win_z - 25, fy - 12.2, win_z + 55, OR, op=0.35)
rect(fy - 7.8, win_z + 25, fy - 7.8 - lead_t, win_z + 55, PB)
rect(fy - 12.8, win_z - 27, fy - 14.8, win_z + 55, OR)
for (a, b) in [(fy, fy-3), (fy-4.2, fy-6.2), (fy-12.8, fy-14.8)]:
    rect(a, win_z - window_d/2 - 1, b, win_z + window_d/2 + 1, "white")
# camini (proiettati)
def chimney(y, z0, L, up):
    sgn = 1 if up else -1
    for s in (-1, 1):
        rect(y + s*(cable_d/2 + 1.2), z0, y + s*(cable_d/2 + 1.2 + lead_t), z0 + sgn*L, PB, op=0.8)
        rect(y + s*(cable_d/2), z0, y + s*(cable_d/2 + 1.2), z0 + sgn*(L + 2), OR, op=0.8)
        rect(y + s*(cable_d/2 + 1.2 + lead_t + 0.6), z0, y + s*(cable_d/2 + 1.2 + lead_t + 2.2), z0 + sgn*(L + 2), OR, op=0.8)
    rect(y - 17, z0, y + 17, z0 + sgn*3, OR, op=0.8)
chimney(hv_y, H + lead_t + 3, hv_L, True)
for z in range(6, hv_L - 12, 12):
    zz = H + lead_t + 3 + z
    out.append(f'<path d="M{X(hv_y-10.4):.1f},{Z(zz):.1f} L{X(hv_y-17.4):.1f},{Z(zz+7):.1f} L{X(hv_y+17.4):.1f},{Z(zz+7):.1f} L{X(hv_y+10.4):.1f},{Z(zz):.1f}" fill="{OR}" fill-opacity="0.5"/>')
chimney(lv_y, 0, lv_L, False)
text(hv_y + 22, H + lead_t + 40, "passante AT piombato", 11)
text(hv_y + 22, H + lead_t + 28, "(fuori asse, proiettato)", 11)
text(-R_pl - 4, -lv_L + 4, "camino BT piombato", 11, "end")
text(-R_pl - 4, -lv_L - 9, "(proiettato)", 11, "end")
# zoccolo, tubo
rect(-28, z_sock - 4, 28, z_sock, OR); rect(-20, floor_t + lead_t, -12, z_sock - 4, OR); rect(12, floor_t + lead_t, 20, z_sock - 4, OR)
rect(-16, z_sock, 16, z_tube, "#222")
r = tube_d/2 - 1
out.append(f'<path d="M{X(-r):.1f},{Z(z_tube):.1f} L{X(-r):.1f},{Z(z_tube+tube_seated_h-22):.1f} '
           f'Q{X(-r):.1f},{Z(z_tube+tube_seated_h-8):.1f} {X(0):.1f},{Z(z_tube+tube_seated_h-8):.1f} '
           f'Q{X(r):.1f},{Z(z_tube+tube_seated_h-8):.1f} {X(r):.1f},{Z(z_tube+tube_seated_h-22):.1f} '
           f'L{X(r):.1f},{Z(z_tube):.1f} Z" fill="#dff4f7" stroke="#6aa" stroke-width="1.2"/>')
ez = z_tube + anode_rim_h
rect(-anode_r, ez, anode_r, ez + 30, "#b8b8b8", "#666")
line(0, ez - 3, 0, ez + 26, "#c60", 2)
rect(-4.5, z_tube + tube_seated_h - 8, 4.5, z_tube + tube_seated_h, "#999", "#555")
for s in (-1, 1): out.append(f'<circle cx="{X(s*anode_r):.1f}" cy="{Z(ez):.1f}" r="5" fill="#e33"/>')
for ang in (-35, -15, 0, 15, 35):
    a = math.radians(ang)
    line(-anode_r - 2, ez, -anode_r - 2 - 38*math.cos(a), ez + 38*math.sin(a), "#e33", 1.6, "5,3", marker=True)
    line(anode_r + 2, ez, anode_r + 2 + 38*math.cos(a), ez + 38*math.sin(a), "#e33", 1.6, "5,3", marker=True)
line(-cav_r, win_z, fy - 40, win_z, "#e33", 3, marker=True)
# raggio "peggiore" verso il passante AT: finisce nel piombo del camino
yb = hv_y - cable_d/2; zb = H + lead_t + 3
sl = (yb - anode_r) / (zb - ez)
line(anode_r, ez, anode_r + sl*(zb + 14 - ez), zb + 14, "#e33", 1, "2,3")
# quote
line(tube_d/2, ez - 8, cav_r, ez - 8, "#06c", 1, "3,2")
text(cav_r + 12, ez - 30, "≥ 35 mm aria vetro → parete", 11, c="#06c")
text(cav_r + 12, ez - 43, "(placca → piombo ≥ 48 mm)", 11, c="#06c")
line(-30, H - top_clear, -30, H, "#06c", 1, "3,2"); text(-28, H - 22, "≥ 40 mm", 11, c="#06c")
# etichette
text(-sl_or - 2, win_z - 42, "finestra Ø20 nei fogli", 11, "end")
text(-sl_or - 2, win_z - 55, "+ membrana stampata 0,8 mm", 11, "end")
text(fy - 7, win_z + 72, "filtro Al + otturatore Pb", 11, "middle")
text(fy - 7, win_z + 60, "(qui: aperto)", 11, "middle")
text(sl_or + 6, ez + 6, "anello di emissione:", 12, c="#c00", bold=True)
text(sl_or + 6, ez - 7, "bordo inferiore della placca", 11, c="#c00")
text(0, z_tube + tube_seated_h + 5, "cappuccio anodico (+AT)", 11, "middle")
text(0, z_sock - 14, "supporto + zoccolo UX4", 11, "middle")
text(sl_or + 6, H - 40, "bicchiere PETG 3 (100%, isolante)", 11)
text(sl_or + 6, H - 53, f"{lead_n} fogli Pb 1 mm avvolti", 11)
text(sl_or + 6, H - 66, "manicotto PETG 2", 11)
text(-sl_or, H + 18, f"coperchio: {lead_n} dischi Pb 1 mm", 11, "start")
text(0, -plinth_h - 16, f"fondo: PETG 4 + {lead_n} dischi Pb (il Pb di parete parte 2 mm sotto)", 11, "middle")

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hpx}" viewBox="0 0 {W} {Hpx}" '
       f'font-family="Helvetica,Arial,sans-serif"><rect width="100%" height="100%" fill="white"/>'
       '<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
       '<path d="M0,0 L8,4 L0,8 Z" fill="#e33"/></marker></defs>'
       f'<text x="20" y="28" font-size="18" font-weight="bold">Case cilindrico 2X2A — sezione (quote in mm)</text>'
       + "".join(out) + "</svg>")
print(svg)
