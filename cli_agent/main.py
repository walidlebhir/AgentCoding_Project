#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cli_agent.utils.config import ENV_API_URL
from cli_agent.utils.logger import info, error, header, step, success, warn
from cli_agent.utils.logger import _color
from cli_agent.core.client import ApiClient
from cli_agent.core.parser import parse_prompt, extract_project_path
from cli_agent.commands import generate, edit, add


def _banner() -> str:
    Y = lambda t: _color(93, t)
    C = lambda t: _color(96, t)
    G = lambda t: _color(90, t)
    B = lambda t: _color(94, t)
    H = "#"
    L = Y(H + H * 42 + H)
    return (
        f"\n  {L}"
        f"\n  {Y(H)}   {C('SPRINGFORGE CLI')}     {G('v3.0')}         {Y(H)}"
        f"\n  {Y(H)} {G('Spring Boot Agentic Generator')}    {Y(H)}"
        f"\n  {L}"
        f"\n  {Y(H)} {B('generate')}  {G('<description>')}  {Y(H)}"
        f"\n  {Y(H)} {B('edit')}      {G('<dir> <changes>')}  {Y(H)}"
        f"\n  {Y(H)} {B('add')}       {G('<feature>')}       {Y(H)}"
        f"\n  {Y(H)} {B('health')}                        {Y(H)}"
        f"\n  {Y(H)} {B('exit')}                          {Y(H)}"
        f"\n  {L}"
    )


def cmd_health(client: ApiClient):
    header("SpringForge — Health Check")
    step("Checking API...")
    h = client.health()
    if h.get("status") == "running":
        success(f"API is {h['status']}")
        info(f"  Version : {h.get('version', '?')}")
        providers = h.get("providers", {})
        for name, state in providers.items():
            s = state.get("state", "?")
            cd = state.get("cooldown_remaining", 0)
            rem = state.get("remaining_daily", 0)
            info(f"  {name:40s} state={s:15s} daily_rem={rem}")
        calls = h.get("call_stats", {})
        info(f"  Global LLM calls: {calls.get('global_calls', 0)}")
    else:
        error(f"API unreachable: {h.get('detail', 'Unknown')}")


def _print_cmd_box():
    B = lambda t: _color(94, t)
    G = lambda t: _color(90, t)
    Y = lambda t: _color(93, t)
    print(f"  {Y('/exit')}   {G('Quit')}")
    print(f"  {Y('/help')}   {G('Show commands')}")
    print(f"  {Y('/health')} {G('API status')}")
    print(f"  {Y('edit:')}   {G('<dir>')} {G('<changes>')}")
    print(f"  {Y('add:')}    {G('<feature>')} {B('--path <dir>')}")


def _repl(client: ApiClient):
    B = lambda t: _color(94, t)
    C = lambda t: _color(96, t)
    G = lambda t: _color(90, t)
    Y = lambda t: _color(93, t)

    q = chr(39)
    print(f"""
  {Y('.----------------------------------------------.')}
  {Y('|')}   {C('SPRINGFORGE CLI')}          {G('v3.0')}           {Y('|')}
  {Y('|')}   {G('Spring Boot Agentic Generator')}        {Y('|')}
  {Y('|')}                                            {Y('|')}
  {Y('|')}   {G('Describe what you want to build:')}        {Y('|')}
  {Y('|')}   {G('"a user management API with JWT auth"')}   {Y('|')}
  {Y('|')}                                            {Y('|')}
  {Y('|')}   {B('/exit')} {G('Exit')}    {B('/help')} {G('Commands')}    {B('/health')} {G('Status')}  {Y('|')}
  {Y(q + '----------------------------------------------' + q)}
""")
    while True:
        try:
            raw = input(f"  {C('-->')} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            info("Goodbye!")
            break
        if not raw:
            continue
        if raw.startswith("/"):
            cmd = raw[1:].strip().lower()
            if cmd in ("exit", "quit", "q"):
                info("Goodbye!")
                break
            if cmd in ("help", "?"):
                _print_cmd_box()
                continue
            if cmd == "health":
                cmd_health(client)
                continue
            warn(f"Unknown command: /{cmd}. Try /help")
            continue

        if raw.startswith("edit "):
            parts = raw[4:].strip().split(None, 1)
            if len(parts) < 2:
                error("Usage: edit <dir> \"<changes>\"")
                continue
            project_dir = parts[0]
            prompt = parse_prompt(parts[1])
            edit.handle(client, project_dir, prompt)
            continue

        if raw.startswith("add "):
            rest = raw[3:].strip()
            path, feature = extract_project_path(rest.split())
            if not feature:
                error("Usage: add \"<feature>\" --path <dir>")
                continue
            feature = parse_prompt(feature)
            add.handle(client, feature, path)
            continue

        path, prompt = extract_project_path(raw.split())
        if prompt:
            prompt = parse_prompt(prompt)
            generate.handle(client, prompt, path)
        else:
            warn("Describe what you want to build.")


def _print_help():
    G = _color(92, "generate")
    E = _color(92, "edit")
    A = _color(92, "add")
    H = _color(92, "health")
    q = chr(34)
    D = _color(90, q + "<description>" + q)
    F = _color(90, q + "<feature>" + q)
    C = _color(90, q + "<changes>" + q)
    P = _color(94, "--path <dir>")
    PD = _color(94, "<project-dir>")
    EX = _color(97, "Examples:")
    print()
    print(f"    {G}    {D}      {P}")
    print(f"    {E}        {PD}   {C}")
    print(f"    {A}         {F}       {P}")
    print(f"    {H}                              Check API status")
    print()
    print(f"  {EX}")
    print()
    print('    generate "user management system"')
    print('    edit ./my-project "add JWT auth"')
    print('    add "payment with Stripe" --path ./my-project')
    print()


def main():
    client = ApiClient(ENV_API_URL)
    args = sys.argv[1:]

    if not args:
        _repl(client)
        return

    if args[0] in ("--help", "-h"):
        print(_banner())
        _print_help()
        return

    command = args[0]

    if command == "health":
        cmd_health(client)
        return

    if command == "generate":
        path, prompt = extract_project_path(args[1:])
        if not prompt:
            print(_banner())
            _print_help()
            return
        prompt = parse_prompt(prompt)
        generate.handle(client, prompt, path)
        return

    if command == "edit":
        if len(args) < 3:
            print(_banner())
            _print_help()
            return
        project_dir = args[1]
        prompt = parse_prompt(" ".join(args[2:]))
        edit.handle(client, project_dir, prompt)
        return

    if command == "add":
        path, feature = extract_project_path(args[1:])
        if not feature:
            print(_banner())
            _print_help()
            return
        feature = parse_prompt(feature)
        add.handle(client, feature, path)
        return

    warn(f"Unknown command: {command}")
    print(_banner())
    _print_help()


if __name__ == "__main__":
    main()
