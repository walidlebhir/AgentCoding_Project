import re


def parse_prompt(raw: str) -> str:
    return raw.strip()


def extract_project_path(args: list[str]) -> tuple[str | None, str]:
    path = None
    parts = list(args)
    for i, a in enumerate(parts):
        if a in ("-p", "--path"):
            if i + 1 < len(parts):
                path = parts.pop(i + 1)
                parts.pop(i)
                break
        if a.startswith("--path="):
            path = a.split("=", 1)[1]
            parts.pop(i)
            break
    return path, " ".join(parts).strip()
