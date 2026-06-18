#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import getpass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from springforge_cli.utils.config import ENV_API_URL
from springforge_cli.utils.logger import _color, info, success, error, warn, step, header
from springforge_cli.core.client import ApiClient
from springforge_cli.core.agent import Agent
from springforge_cli.core.auth_manager import get_auth_manager
from springforge_cli.core.parser import parse_prompt, extract_project_path
from springforge_cli.ui.terminal import TerminalUI, Spinner, Message, render_progress
from springforge_cli.commands import generate, edit, add, fix


def dispatch(agent: Agent, auth_mgr, ui: TerminalUI, raw: str) -> bool:
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
        
        # Authentication commands
        if cmd == "login":
            cmd_login(auth_mgr, ui)
            return True
        if cmd == "register":
            cmd_register(auth_mgr, ui)
            return True
        if cmd == "logout":
            cmd_logout(auth_mgr, ui)
            return True
        if cmd == "user":
            cmd_user(auth_mgr, ui)
            return True
        if cmd == "users":
            cmd_list_users(auth_mgr, ui)
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
        ui.update_status(mode="add")
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
        ui.update_status(mode="fix")
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


def cmd_login(auth_mgr, ui: TerminalUI) -> bool:
    """Handle user login."""
    Message.info("Login to SpringForge Agent")
    email = input("Email: ").strip()
    if not email:
        Message.error("Email is required")
        return False
    
    password = getpass.getpass("Password: ")
    if not password:
        Message.error("Password is required")
        return False
    
    if auth_mgr.login(email, password):
        return True
    return False


def cmd_register(auth_mgr, ui: TerminalUI) -> bool:
    """Handle user registration."""
    Message.info("Register new user")
    name = input("Full Name: ").strip()
    if not name:
        Message.error("Name is required")
        return False
    
    email = input("Email: ").strip()
    if not email:
        Message.error("Email is required")
        return False
    
    password = getpass.getpass("Password: ")
    if not password or len(password) < 6:
        Message.error("Password must be at least 6 characters")
        return False
    
    confirm = getpass.getpass("Confirm Password: ")
    if password != confirm:
        Message.error("Passwords do not match")
        return False
    
    if auth_mgr.register(name, email, password):
        Message.info("Now logging in...")
        return auth_mgr.login(email, password)
    return False


def cmd_logout(auth_mgr, ui: TerminalUI) -> bool:
    """Handle user logout."""
    if not auth_mgr.is_authenticated():
        Message.warn("No user is currently logged in")
        return False
    
    current_user = auth_mgr.get_current_user()
    confirm = input(f"Logout from {current_user}? (y/n): ").strip().lower()
    if confirm == "y":
        return auth_mgr.logout()
    else:
        Message.info("Logout cancelled")
        return False


def cmd_user(auth_mgr, ui: TerminalUI) -> bool:
    """Show current user info."""
    if auth_mgr.is_authenticated():
        current_user = auth_mgr.get_current_user()
        Message.info(f"Current user: {current_user}")
        return True
    else:
        Message.warn("No user is logged in. Use /login to authenticate.")
        return False


def cmd_list_users(auth_mgr, ui: TerminalUI) -> bool:
    """List all stored users."""
    users = auth_mgr.list_users()
    current = auth_mgr.get_current_user()
    if not users:
        Message.info("No users stored")
        return False
    
    Message.info(f"Stored users ({len(users)}):")
    for user in users:
        marker = " *" if user == current else ""
        Message.info(f"  - {user}{marker}")
    return True


def main():
    client = ApiClient(ENV_API_URL)
    agent = Agent(client)
    auth_mgr = get_auth_manager(ENV_API_URL)
    ui = TerminalUI()

    args = sys.argv[1:]

    if not args:
        ui.clear_screen()
        ui.show_welcome()
        running = True
        while running:
            try:
                raw = ui.get_input()
                running = dispatch(agent, auth_mgr, ui, raw)
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

    # Authentication commands
    if command == "login":
        cmd_login(auth_mgr, ui)
        return
    
    if command == "register":
        cmd_register(auth_mgr, ui)
        return
    
    if command == "logout":
        cmd_logout(auth_mgr, ui)
        return
    
    if command == "user":
        cmd_user(auth_mgr, ui)
        return
    
    if command == "users":
        cmd_list_users(auth_mgr, ui)
        return

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
