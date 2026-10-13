"""Gerber -> black solder-mask texture (top or bottom) + plated holes list.
   tex.py <gerber_prefix> <cu> <mask> <silk> <edge> <out.png> [holes.json] [drl]"""
import io, json, sys, numpy as np
from PIL import Image
import cairosvg
from gerbonara import GerberFile, ExcellonFile
pre, cu_n, mo_n, sk_n, ed_n, out = sys.argv[1:7]
(x0, y0), (x1, y1) = GerberFile.open(pre + ed_n).bounding_box()
x0, y0, x1, y1 = [round(v, 2) for v in (x0 + 0.05, y0 + 0.05, x1 - 0.05, y1 - 0.05)]
B = ((x0, y0), (x1, y1)); PX = 20
W, H = int(round((x1 - x0) * PX)), int(round((y1 - y0) * PX))
def ras(name):
    svg = str(GerberFile.open(pre + name).to_svg(force_bounds=B, fg='black', bg='white'))
    a = np.array(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=W, output_height=H))).convert('RGBA'))
    return (a[:, :, 3] > 128) & (a[:, :, :3].mean(2) < 128)
cu, mo, sk = ras(cu_n), ras(mo_n), ras(sk_n)
img = np.zeros((H, W, 3), np.uint8); img[:] = (14, 14, 15)
img[cu] = (30, 30, 32)
img[sk & ~mo] = (240, 240, 234)
img[mo] = (214, 211, 200)
holes = []
if len(sys.argv) > 8:
    d = ExcellonFile.open(pre + sys.argv[8])
    holes = [(round(o.x, 3), round(o.y, 3), round(o.tool.diameter, 3)) for o in d.objects if hasattr(o, 'x')]
    holes += [(round((o.x1 + o.x2) / 2, 3), round((o.y1 + o.y2) / 2, 3), round(o.aperture.diameter, 3)) for o in d.objects if not hasattr(o, 'x')]
    yy, xx = np.mgrid[0:H, 0:W]
    for x, y, dia in holes:
        cx, cy = (x - x0) * PX, (y1 - y) * PX; r = dia / 2 * PX
        a0, a1 = max(0, int(cx - r - 2)), int(cx + r + 3); b0, b1 = max(0, int(cy - r - 2)), int(cy + r + 3)
        sub = (xx[b0:b1, a0:a1] - cx) ** 2 + (yy[b0:b1, a0:a1] - cy) ** 2 < r * r
        img[b0:b1, a0:a1][sub] = (6, 6, 6)
    json.dump([(x, -y, dd) for x, y, dd in holes], open(sys.argv[7], 'w'))
Image.fromarray(img).save(out)
print(out, B, img.shape, len(holes))
