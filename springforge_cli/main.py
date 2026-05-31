#!/usr/bin/env python3
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from springforge_cli.utils.config import ENV_API_URL
from springforge_cli.utils.logger import _color, info, success, error, warn, step, header
from springforge_cli.core.client import ApiClient
from springforge_cli.core.agent import Agent
from springforge_cli.core.parser import parse_prompt, extract_project_path
from springforge_cli.ui.terminal import TerminalUI, Spinner, Message, render_progress
from springforge_cli.commands import generate, edit, add, fix


def dispatch(agent: Agent, ui: TerminalUI, raw: str) -> bool:
    raw = raw.strip()
    if not raw:
        return True

    if raw.startswith("/"):
        cmd = raw[1:].strip().lower()
        if cmd in ("exit", "quit", "q"):
            Message.assistant("Goodbye!")
            return False
        if cmd in ("help", "?"):
            ui.show_help()
            return True
        if cmd == "health":
            cmd_health(agent, ui)
            return True
        Message.error(f"Unknown command: /{cmd}. Type /help for commands.")
        return True

    Message.user(raw)

    if raw.startswith("edit "):
        parts = raw[4:].strip().split(None, 1)
        if len(parts) < 2:
            Message.error("Usage: edit <dir> \"<changes>\"")
            return True
        project_dir = parts[0]
        prompt_text = parse_prompt(parts[1])
        ui.update_status(mode="edit")
        render_progress(["Analyzing project structure...", "Applying modifications..."])
        result = edit.handle(agent, project_dir, prompt_text)
        if result:
            Message.result(True, "Project modified successfully")
        else:
            Message.result(False, "Edit failed")
        ui.update_status(mode="generate")
        return True

    if raw.startswith("add "):
        rest = raw[3:].strip()
        path, feature = extract_project_path(rest.split())
        if not feature:
            Message.error("Usage: add \"<feature>\" [--path <dir>]")
            return True
        feature = parse_prompt(feature)
        ui.update_status(mode="add")
        render_progress(["Analyzing project...", "Integrating new feature..."])
        result = add.handle(agent, feature, path)
        if result:
            Message.result(True, f"Feature '{feature}' added")
        else:
            Message.result(False, "Failed to add feature")
        ui.update_status(mode="generate")
        return True

    if raw.startswith("fix "):
        rest = raw[3:].strip()
        path, bug_desc = extract_project_path(rest.split())
        if not bug_desc:
            Message.error("Usage: fix \"<bug description>\" [--path <dir>]")
            return True
        bug_desc = parse_prompt(bug_desc)
        ui.update_status(mode="fix")
        render_progress(["Analyzing bug report...", "Scanning codebase...", "Applying fix..."])
        result = fix.handle(agent, bug_desc, path)
        if result:
            Message.result(True, "Bug fixed successfully")
        else:
            Message.result(False, "Failed to fix bug")
        ui.update_status(mode="generate")
        return True

    path, prompt_text = extract_project_path(raw.split())
    if prompt_text:
        prompt_text = parse_prompt(prompt_text)
        ui.update_status(mode="generate")
        render_progress(["Analyzing request...", "Generating Spring Boot architecture...", "Writing files..."])
        result = generate.handle(agent, prompt_text, path)
        if result:
            Message.result(True, "Project generated successfully")
        else:
            Message.result(False, "Generation failed")
        ui.update_status(mode="generate")
    else:
        Message.info("Describe what you want to build, or type /help")

    return True


def cmd_health(agent: Agent, ui: TerminalUI) -> bool:
    with Spinner("Checking API..."):
        h = agent.health()
    if h.get("status") == "running":
        Message.result(True, f"API is {h['status']} (v{h.get('version', '?')})")
        providers = h.get("providers", {})
        for name, state in providers.items():
            s = state.get("state", "?")
            rem = state.get("remaining_daily", 0)
            Message.info(f"{name:35s} state={s:15s} daily_rem={rem}")
        calls = h.get("call_stats", {})
        Message.info(f"Global LLM calls: {calls.get('global_calls', 0)}")
    else:
        Message.error(f"API unreachable: {h.get('detail', 'Unknown')}")
    return True


def main():
    client = ApiClient(ENV_API_URL)
    agent = Agent(client)
    ui = TerminalUI()

    args = sys.argv[1:]

    if not args:
        ui.clear_screen()
        ui.show_welcome()
        running = True
        while running:
            try:
                raw = ui.get_input()
                running = dispatch(agent, ui, raw)
            except (EOFError, KeyboardInterrupt):
                print()
                Message.assistant("Goodbye!")
                break
        return

    if args[0] in ("--help", "-h"):
        ui.clear_screen()
        ui.show_welcome()
        return

    command = args[0]

    if command == "health":
        cmd_health(agent, ui)
        return

    prompt_text = parse_prompt(" ".join(args[1:]))

    if command == "generate":
        if not prompt_text:
            ui.clear_screen()
            ui.show_welcome()
            return
        Message.user(f"generate {prompt_text}")
        ui.update_status(mode="generate")
        render_progress(["Analyzing request...", "Generating Spring Boot architecture...", "Writing files..."])
        result = generate.handle(agent, prompt_text, None)
        Message.result(result, "Project generated successfully" if result else "Generation failed")
        return

    if command == "edit":
        if len(args) < 3:
            ui.clear_screen()
            ui.show_welcome()
            return
        project_dir = args[1]
        Message.user(f"edit {project_dir} {prompt_text}")
        ui.update_status(mode="edit")
        render_progress(["Analyzing project structure...", "Applying modifications..."])
        result = edit.handle(agent, project_dir, prompt_text)
        Message.result(result, "Edit completed" if result else "Edit failed")
        return

    if command == "add":
        if not prompt_text:
            ui.clear_screen()
            ui.show_welcome()
            return
        Message.user(f"add {prompt_text}")
        ui.update_status(mode="add")
        render_progress(["Analyzing project...", "Integrating new feature..."])
        result = add.handle(agent, prompt_text, None)
        Message.result(result, f"Feature added" if result else "Add failed")
        return

    if command == "fix":
        if not prompt_text:
            ui.clear_screen()
            ui.show_welcome()
            return
        Message.user(f"fix {prompt_text}")
        ui.update_status(mode="fix")
        render_progress(["Analyzing bug report...", "Scanning codebase...", "Applying fix..."])
        result = fix.handle(agent, prompt_text, None)
        Message.result(result, "Bug fixed" if result else "Fix failed")
        return

    Message.error(f"Unknown command: {command}")
    ui.show_help()


if __name__ == "__main__":
    main()
