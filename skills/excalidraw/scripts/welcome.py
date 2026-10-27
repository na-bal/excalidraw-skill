#!/usr/bin/env python3
"""The first board a new user sees: a short note from the author and three tips.
Drawn by the skill itself, so it doubles as a demo. Deleting it changes nothing.

  welcome.py out.excalidraw [--lang ru|en]   (default: from $LANG)

Plan: one idea — "your agent draws here, you fix by hand, it learns". Zones top to
bottom: greeting + robot, note from the author with a hand signature, three tip
cards in a row, a quiet footer about reporting bugs. Width ~1000 px.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scene import box, text, save
from stamps import stamp

TEXT = {
    "en": {
        "title": "Hi! This board was drawn by your agent",
        "note": ["I made this skill for myself, to stop explaining",
                 "systems in words. Now it's yours — draw a lot."],
        "sign": "— Alexander Bedelev",
        "tips": [["Ask for a picture", "“draw how our", "signup works”"],
                 ["Fix it by hand", "your edits are never", "overwritten"],
                 ["Say what's off", "“less color” — it", "remembers next time"]],
        "footer": "Something broken? Ask your agent to report it to the author — it shows you the report first.",
    },
    "ru": {
        "title": "Привет! Эту доску нарисовал твой агент",
        "note": ["Я сделал этот скилл для себя, чтобы не объяснять",
                 "системы словами. Теперь он твой — рисуй побольше."],
        "sign": "— Александр Беделев",
        "tips": [["Попроси картинку", "«нарисуй, как у нас", "устроена регистрация»"],
                 ["Поправь руками", "твои правки агент", "не затрёт"],
                 ["Скажи, что не так", "«поменьше цвета» —", "запомнит на будущее"]],
        "footer": "Что-то сломалось? Попроси агента отправить отчёт автору — он сначала покажет его тебе.",
    },
}


def build(lang):
    t = TEXT[lang]
    E = [text(0, 0, t["title"], font_size=36)]
    E += stamp("robot", 920, -10, h=190)
    for i, line in enumerate(t["note"]):
        E.append(text(0, 80 + i * 30, line, font_size=22, color="#495057"))
    E.append(text(380, 150, t["sign"], font_size=28, color="#1971c2"))
    fills = ["#a5d8ff", "#b2f2bb", "#ffec99"]
    for i, (head, *rest) in enumerate(t["tips"]):
        E += box(i * 340, 240, 300, [head, "", *rest], fill=fills[i], font_size=20)
    E.append(text(0, 420, t["footer"], font_size=16, color="#868e96"))
    return E


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--lang", choices=sorted(TEXT))
    a = ap.parse_args()
    lang = a.lang or ("ru" if os.environ.get("LANG", "").startswith("ru") else "en")
    print(save(a.out, build(lang)))
