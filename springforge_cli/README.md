# SPRINGFORGE CLI

Your Spring Boot AI Coding Assistant in the Terminal.

## Installation

```powershell
cd springforge_cli
pip install -r requirements.txt
```

## Usage

### Interactive mode (REPL)
```powershell
python main.py
```

### Direct commands
```powershell
python main.py generate "user management system"
python main.py edit ./project "add JWT authentication"
python main.py add "payment with Stripe" --path ./project
python main.py fix "NullPointerException in UserService"
python main.py health
python main.py --help
```

## Configuration

Set environment variables:
- `SPRINGFORGE_API_URL` — Backend API URL (default: http://localhost:8000)
- `SPRINGFORGE_MODEL` — Active LLM model name (default: gemini-2.5-flash)
