"""Sheet of quick stamps: STAMPS_NO_USAGE=1 python3 quick_sheet.py out.excalidraw"""
import sys
from scene import text, save
from stamps import stamp, QUICK, LIB, bbox, resolve

E = [text(30, -50, "Quick stamps: stamp(\"name\", x, y, w=…)", font_size=22)]
for i, (n, v) in enumerate(QUICK.items()):
    x, y = 30 + (i % 8) * 140, 30 + (i // 8) * 150
    key, bare = resolve(n)
    els = stamp(n, 0, 0)
    bx, by, bw, bh = bbox(els)
    s = min(100 / bw, 80 / bh)
    E += stamp(n, x + (100 - bw * s) / 2, y, w=bw * s)
    E.append(text(x, y + 92, n, font_size=16, color="#1971c2"))
save(sys.argv[1] if len(sys.argv) > 1 else "quick.excalidraw", E)
