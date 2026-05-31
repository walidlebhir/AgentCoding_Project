import os
import sys
import time
import threading
import shutil
from springforge_cli.utils.logger import _color
from springforge_cli.utils.config import ENV_API_URL, ACTIVE_MODEL


def _rgb(r: int, g: int, b: int, text: str) -> str:
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


def _dim(text: str) -> str:
    return f"\033[2m{text}\033[0m"


def _bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"


G = lambda t: f"\033[90m{t}\033[0m"
W = lambda t: f"\033[97m{t}\033[0m"
C = lambda t: f"\033[96m{t}\033[0m"
Y = lambda t: f"\033[93m{t}\033[0m"
B = lambda t: f"\033[94m{t}\033[0m"
GR = lambda t: f"\033[92m{t}\033[0m"
M = lambda t: f"\033[95m{t}\033[0m"
R = lambda t: f"\033[91m{t}\033[0m"


DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"


class Spinner:
    def __init__(self, message: str = ""):
        self.message = message
        self._running = False
        self._thread = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
        sys.stdout.write("\r" + " " * shutil.get_terminal_size().columns + "\r")
        sys.stdout.flush()

    def _spin(self):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        idx = 0
        while self._running:
            frame = frames[idx % len(frames)]
            msg = self.message[: shutil.get_terminal_size().columns - 10]
            sys.stdout.write(f"\r  {C(frame)} {_dim(msg)}")
            sys.stdout.flush()
            time.sleep(0.08)
            idx += 1


class Message:
    @staticmethod
    def user(text: str):
        ts = _dim(time.strftime("%H:%M"))
        term = shutil.get_terminal_size().columns
        line = _dim("─" * (term - 2))
        print(f"\n  {ts}  {BOLD}{W('You:')}{RESET} {W(text)}")
        print(f"  {line}")

    @staticmethod
    def assistant(text: str):
        ts = _dim(time.strftime("%H:%M"))
        print(f"  {ts}  {BOLD}{GR('SpringForge:')}{RESET} {W(text)}")

    @staticmethod
    def divider():
        term = shutil.get_terminal_size().columns
        print(f"  {_dim('─' * (term - 2))}")

    @staticmethod
    def result(success_flag: bool, text: str):
        icon = GR("✔") if success_flag else R("✘")
        label = GR("Success") if success_flag else R("Error")
        print(f"  {icon}  {W(text)}  {_dim(f'· {label}')}")

    @staticmethod
    def info(text: str):
        print(f"  {C('ℹ')}  {_dim(text)}")

    @staticmethod
    def error(text: str):
        print(f"  {R('✘')}  {R(text)}")


class TerminalUI:
    def __init__(self):
        self.current_dir = os.getcwd()
        self.active_model = ACTIVE_MODEL
        self.mode = "generate"

    def show_welcome(self):
        term = shutil.get_terminal_size().columns
        cy = lambda t: _rgb(56, 189, 248, t)
        te = lambda t: _rgb(34, 211, 238, t)
        pu = lambda t: _rgb(129, 140, 248, t)
        g1 = lambda t: _rgb(75, 85, 99, t)
        g2 = lambda t: _rgb(156, 163, 175, t)
        g3 = lambda t: _rgb(209, 213, 219, t)

        logo = (
            f"\n"
            f"\n     {cy('███████╗██████╗ ██████╗ ██╗███╗   ██╗ ██████╗')}"
            f"\n     {cy('██╔════╝██╔══██╗██╔══██╗██║████╗  ██║██╔════╝')}"
            f"\n     {cy('███████╗██████╔╝██████╔╝██║██╔██╗ ██║██║  ███╗')}"
            f"\n     {cy('╚════██║██╔══██╗██╔══██╗██║██║╚██╗██║██║   ██║')}"
            f"\n     {cy('███████║██║  ██║██║  ██║██║██║ ╚████║╚██████╔╝')}"
            f"\n     {cy('╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝')}"
            f"\n"
            f"\n            {_bold(cy('SPRINGFORGE CLI'))}"
            f"\n            {_dim('Your Spring Boot AI Coding Assistant')}"
        )
        print(logo)

        model_str = self.active_model
        mode_str = self.mode.upper()
        api_str = ENV_API_URL.replace("http://", "").replace("https://", "")

        footer = (
            f"\n  {g1('┌─')} {g2('STATUS')} {g1('─' * (term - 22))}┐"
            f"\n  {g1('│')}   {g2('▸')}  {g3('folder:')} {W(os.path.basename(self.current_dir))}  "
            f"{g2('·')}  {g3('mode:')} {Y(mode_str)}  "
            f"{g2('·')}  {g3('model:')} {te(model_str)}  "
            f"{g2('·')}  {g3('api:')} {cy(api_str)}"
            f"\n  {g1('└─')}{g1('─' * (term - 22))}┘"
        )
        print(footer)

        print(f"\n  {g2('▸')}  {_bold(g3('Getting Started'))}")
        print(f"  {g1('─' * (term - 4))}")
        tips = [
            (f"{cy('✦')}  {g3('Generate projects')}  {_dim('—')}  {g2('Describe your Spring Boot app in plain English')}"),
            (f"{cy('✦')}  {g3('Edit codebases')}    {_dim('—')}  {g2('Tell the agent what to change, it handles the rest')}"),
            (f"{cy('✦')}  {g3('Add features')}      {_dim('—')}  {g2('New payment system? Just describe it naturally')}"),
            (f"{cy('✦')}  {g3('Fix bugs')}          {_dim('—')}  {g2('Describe the issue, let AI find and patch it')}"),
        ]
        for t in tips:
            print(f"  {t}")
        print(f"  {g1('─' * (term - 4))}")
        print(f"  {_dim('Type')} {cy('/help')} {_dim('for all commands  ·  Type')} {cy('/exit')} {_dim('to quit')}")
        print()
        Message.divider()

    def update_status(self, mode: str | None = None, model: str | None = None):
        if mode:
            self.mode = mode
        if model:
            self.active_model = model

    def get_input(self) -> str:
        try:
            prompt = f"  {BOLD}{C('┃')}{RESET}  "
            return input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return "/exit"

    def show_help(self):
        term = shutil.get_terminal_size().columns
        print(f"\n  {_bold(W('Commands'))}")
        print(f"  {_dim('─' * (term - 2))}")
        cmds = [
            ("generate <desc>", "Generate a Spring Boot project"),
            ("edit <dir> <desc>", "Modify an existing project"),
            ("add <feature> [--path <dir>]", "Add a new feature"),
            ("fix <bug-desc> [--path <dir>]", "Fix a bug in the codebase"),
            ("health", "Check API and provider status"),
            ("/help", "Show this help message"),
            ("/exit", "Exit the CLI"),
        ]
        for cmd, desc in cmds:
            print(f"  {C(cmd):40s} {_dim(desc)}")
        print(f"\n  {_bold(W('Examples'))}")
        print(f"  {_dim('─' * (term - 2))}")
        examples = [
            ('generate "user management system"', None),
            ('edit ./my-project "add JWT authentication"', None),
            ('add "payment with Stripe" --path ./my-project', None),
            ('fix "NullPointerException in UserService"', None),
        ]
        for ex, _ in examples:
            print(f"  {GR(ex)}")
        print()

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")


def render_progress(steps: list[str]):
    for msg in steps:
        with Spinner(msg):
            time.sleep(0.5)
