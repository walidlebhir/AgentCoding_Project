import sys
from datetime import datetime


def _color(code: int, text: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def info(msg: str):
    print(f"  {_color(94, '*')} {msg}")


def success(msg: str):
    print(f"  {_color(92, '+')} {msg}")


def warn(msg: str):
    print(f"  {_color(93, '!')} {msg}", file=sys.stderr)


def error(msg: str):
    print(f"  {_color(91, 'x')} {msg}", file=sys.stderr)


def step(msg: str):
    print(f"  {_color(96, '>')} {msg}")


def header(msg: str):
    L = _color(95, "---")
    print(f"\n {L} {_color(97, msg)} {L}\n")
