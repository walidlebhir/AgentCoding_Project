import re
import os


def parse_prompt(raw: str) -> str:
    return raw.strip().strip('"\'')


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


def parse_llm_response(text: str) -> list[dict]:
    files = []
    pattern = re.compile(
        r"<<<FILE:([^\n]+?)>>>\s*\n(.*?)\n\s*<<<END_FILE>>>",
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        filepath = match.group(1).strip()
        content = match.group(2)
        files.append({"path": filepath, "content": content})
    return files


def parse_diff_response(text: str) -> list[dict]:
    changes = []
    pattern = re.compile(
        r"<<<CHANGE:([^\n]+?)>>>\s*\n(.*?)\n\s*<<<END_CHANGE>>>",
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        filepath = match.group(1).strip()
        content = match.group(2)
        changes.append({"path": filepath, "content": content, "type": "modify"})
    pattern2 = re.compile(
        r"<<<DELETE:([^\n]+?)>>>\s*\n(.*?)\n\s*<<<END_DELETE>>>",
        re.DOTALL,
    )
    for match in pattern2.finditer(text):
        filepath = match.group(1).strip()
        content = match.group(2)
        changes.append({"path": filepath, "content": content, "type": "delete"})
    return changes
