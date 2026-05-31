import sys
from datetime import datetime


def _color(code: int, text: str) -> str:
    return f"\033[{code}m{text}\033[0m"


C = lambda t: _color(96, t)
G = lambda t: _color(90, t)
Y = lambda t: _color(93, t)
R = lambda t: _color(91, t)
B = lambda t: _color(94, t)
W = lambda t: _color(97, t)
M = lambda t: _color(95, t)


def _prefix(symbol: str, color_fn, text: str):
    ts = G(datetime.now().strftime("%H:%M:%S"))
    print(f"  {ts} {color_fn(symbol)} {text}")


def info(text: str):
    _prefix("ℹ", C, text)


def success(text: str):
    _prefix("✔", lambda t: _color(92, t), text)


def warn(text: str):
    _prefix("⚠", Y, text)


def error(text: str):
    _prefix("✘", R, text)


def step(text: str):
    _prefix("→", B, text)


def header(text: str):
    h = _color(95, "=" * 56)
    print(f"\n  {h}")
    print(f"  {_color(97, text)}")
    print(f"  {h}\n")


def divider():
    print(f"  {_color(90, '-' * 52)}")
