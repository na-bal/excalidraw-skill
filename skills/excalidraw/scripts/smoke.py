#!/usr/bin/env python3
"""Smallest real diagram, used by setup.sh to prove the pipeline works.

  smoke.py out.excalidraw
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scene import box, connect, text, save

E = [text(40, 0, "It works: agent → scene → board", font_size=28)]
a = box(40, 80, 220, "Your agent", fill="#a5d8ff")
b = box(360, 80, 220, "scene.py", fill="#ffec99")
c = box(680, 80, 220, "Your board", fill="#b2f2bb")
E += a + b + c
E += [connect(a[0], b[0]), connect(b[0], c[0])]
print(save(sys.argv[1] if len(sys.argv) > 1 else "smoke.excalidraw", E))
