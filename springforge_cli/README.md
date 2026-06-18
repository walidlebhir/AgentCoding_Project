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

## LLM Marker/Comment System — File Generation & Code Insertion

The agent CLI uses a **marker-based comment system** to convert LLM output into files and code modifications. Instead of using CrewAI tools, the LLM emits delimited blocks in its response text, which are parsed locally.

### 1. Creating Files (`<<<FILE:path>>>`)

The LLM wraps each file's content between `<<<FILE:path>>>` and `<<<END_FILE>>>` markers:

```
<<<FILE:src/main/java/com/example/demo/User.java>>>
package com.example.demo.entity;

import jakarta.persistence.*;
import lombok.Data;

@Entity
@Data
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;
    private String email;
}
<<<END_FILE>>>
```

**How it works:**
1. The LLM response is scanned with regex: `<<<FILE:(.+)>>>(.*?)<<<END_FILE>>>`
2. Each match extracts the file path and its content
3. Files are written to disk with full directory creation (`os.makedirs`)

### 2. Inserting/Modifying Code (`<<<CHANGE:path>>>`)

For edits and fixes, the LLM uses a `<<<CHANGE:path>>>` marker to specify file modifications:

```
<<<CHANGE:src/main/java/com/example/demo/service/UserService.java>>>
package com.example.demo.service;
// ... modified content ...
<<<END_CHANGE>>>
```

Parsed by `parse_diff_response()` in `springforge_cli/core/parser.py:38` with regex: `<<<CHANGE:(.+)>>>(.*?)<<<END_CHANGE>>>`

### 3. Deleting Code (`<<<DELETE:path>>>`)

The LLM can specify files or code sections to delete:

```
<<<DELETE:src/main/java/com/example/demo/old/DeprecatedClass.java>>>
<<<END_DELETE>>>
```

Parsed with regex: `<<<DELETE:(.+)>>>(.*?)<<<END_DELETE>>>`

### 4. Parsing Flow

```
LLM Response Text
       │
       ▼
parse_llm_response() / parse_diff_response()
  ┌──────────────────────────────┐
  │  regex finditer()            │
  │  → list of {path, content}   │
  └──────────┬───────────────────┘
             ▼
_write_project() / apply_changes()
  ┌──────────────────────────────┐
  │  os.makedirs(parent, exist)  │
  │  open(path, "w").write(code) │
  └──────────────────────────────┘
             ▼
       Files on disk
```

### 5. CrewAI Tool Approach (Alternative)

An alternative approach (see `main.py` at project root) uses a CrewAI `@tool` decorator:

```python
@tool("Create Python File")
def CreateFilePython(directoryName: str, filename: str, code: str) -> str:
    """Create a python file from generated code."""
    full_dir = os.path.join(BASE_DIR, "output", directoryName)
    os.makedirs(full_dir, exist_ok=True)
    filepath = os.path.join(full_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)
    return f"File created: {filepath}"
```

The LLM **calls the tool directly** with parameters (directory, filename, code). This approach is older and requires the LLM to invoke a function call, whereas the marker-based approach (`<<<FILE:path>>>`) is simpler, stateless, and avoids tool-calling issues.

## Configuration

Set environment variables:
- `SPRINGFORGE_API_URL` — Backend API URL (default: http://localhost:8000)
- `SPRINGFORGE_MODEL` — Active LLM model name (default: gemini-2.5-flash)
