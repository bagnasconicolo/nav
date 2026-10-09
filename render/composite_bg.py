import sys
from PIL import Image
import numpy as np
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGBA')
w, h = im.size
yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
cx, cy = w * 0.5, h * 0.42
r = np.sqrt(((xx - cx) / w) ** 2 + ((yy - cy) / h) ** 2)
v = 246 - 26 * np.clip(r / 0.75, 0, 1) ** 1.6
bg = np.stack([v, v, v + 1.5], -1).clip(0, 255).astype(np.uint8)
bgi = Image.fromarray(bg, 'RGB').convert('RGBA')
out = Image.alpha_composite(bgi, im).convert('RGB')
out.save(dst, quality=95)
