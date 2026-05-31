import os
import re
import time
import hashlib
import json
import shutil
from datetime import datetime

# Architecture mono-appel (v3) : remplace l'ancien pipeline CrewAI multi-agents.
# Avant : 4 agents CrewAI (Architect, Builder, Coder, Docs) avec boucles ReAct
#         généraient 12-40 appels LLM par projet → erreurs 429 quasi-systématiques.
# Maintenant : 1 unique appel LLM → parsing local → tous les fichiers projet.
# Le seul composant CrewAI conservé est la classe LLM (config.py) pour sa couche
# d'abstraction multi-fournisseur (Gemini natif + LiteLLM).
from src.System_Agentic.rate_limiter import get_manager, SORTED_MODELS, PROVIDER_CONFIG, LimiterState
from src.System_Agentic.config import create_llm, OUTPUT_DIR

_CACHE: dict[str, tuple[str, float, str]] = {}
_CACHE_TTL = 7200

TOTAL_RETRIES = 3

SYSTEM_PROMPT = """You are a Spring Boot expert. Generate a complete Java Spring Boot application.

Rules:
- Return ALL files of the project, one by one, using the exact delimiter format below.
- Every file must start with <<<FILE:path/to/file.java>>> and end with <<<END_FILE>>>.
- Include: pom.xml, Application.java, entities, repositories, services, controllers, DTOs, application.properties.
- Use Java 17+, Spring Boot 3.x, Maven, Spring Data JPA, H2 or PostgreSQL, Spring Web.
- Package structure: {group_id}.{project_name}
- The code must be complete, compilable, and production-ready.

Format:
<<<FILE:pom.xml>>>
<?xml version="1.0" encoding="UTF-8"?>
...
<<<END_FILE>>>
<<<FILE:src/main/java/com/example/demo/DemoApplication.java>>>
package com.example.demo;
...
<<<END_FILE>>>
"""


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:32]


def _project_id() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    import random
    return f"proj_{ts}_{random.randint(1000,9999)}"


def _build_prompt(user_prompt: str) -> str:
    return f"""{SYSTEM_PROMPT}

User request: {user_prompt}

Generate ALL files for this Spring Boot project using the <<<FILE:path>>>...<<<END_FILE>>> format.
Do NOT add any explanation before or after the files."""


def _parse_files(text: str) -> list[dict]:
    files = []
    pattern = re.compile(
        r"<<<\s*FILE\s*:\s*(.+?)\s*>>>\s*(.*?)\s*<<<\s*END_FILE\s*>>>",
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        path = m.group(1).strip().replace("\\", "/")
        content = m.group(2).strip()
        if path and content:
            files.append({"path": path, "content": content})
    return files


def _write_project(project_dir: str, files: list[dict]) -> int:
    written = 0
    for f in files:
        abs_path = os.path.join(project_dir, f["path"])
        parent = os.path.dirname(abs_path)
        os.makedirs(parent, exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as fh:
            fh.write(f["content"])
        written += 1
    return written


def generate_project(user_prompt: str, request_id: str = "") -> dict:
    mgr = get_manager()

    cache_key = _hash(user_prompt)
    if cache_key in _CACHE:
        cached_pid, ts, _ = _CACHE[cache_key]
        if time.time() - ts < _CACHE_TTL:
            return {
                "success": True,
                "project_id": cached_pid,
                "cached": True,
                "files": 0,
                "provider": "cache",
                "llm_calls": 0,
            }
        del _CACHE[cache_key]

    project_id = _project_id()
    project_dir = os.path.join(OUTPUT_DIR, project_id)
    last_error = ""
    call_count = 0
    used_model = ""

    prompt = _build_prompt(user_prompt)

    for attempt in range(TOTAL_RETRIES):
        model = mgr.get_best()
        if not model:
            msg = "All providers exhausted"
            if last_error:
                msg += f" | last: {last_error[:150]}"
            return {"success": False, "error": msg, "project_id": project_id, "llm_calls": call_count}

        used_model = model
        llm = create_llm(model)
        if not llm:
            mgr._get(model).state = LimiterState.QUOTA_EXCEEDED
            mgr._get(model).cooldown_until = time.time() + 86400
            continue

        call_count += 1
        try:
            # Appel LLM unique via CrewAI LLM.
            # La méthode .call() est l'interface unifiée commune à tous les fournisseurs :
            #   - GeminiCompletion (préfixe "gemini/") utilise le SDK Google natif
            #   - LiteLLM (préfixe "groq/") utilise l'API Groq
            # Contrairement à l'ancienne architecture multi-agents (CrewAI Agent/Crew/Tasks)
            # qui multipliait les appels via la boucle ReAct (max_iter=25 par agent),
            # ici un seul appel suffit pour générer l'intégralité du projet.
            result = llm.call(prompt)
            text = result if isinstance(result, str) else str(result)
        except Exception as e:
            msg = str(e)
            last_error = msg[:300]

            if "429" in msg or "quota" in msg.lower() or "resource_exhausted" in msg.lower():
                wait = _extract_wait(msg)
                is_daily = _is_daily_quota(msg)
                mgr.record_429(model, msg, wait, is_daily=is_daily)
                if is_daily:
                    continue
                if wait < 60:
                    time.sleep(wait + 1)
                    continue
                else:
                    continue
            else:
                return {
                    "success": False,
                    "error": f"LLM error on {model}: {msg[:200]}",
                    "project_id": project_id,
                    "llm_calls": call_count,
                }

        files = _parse_files(text)
        if not files:
            last_error = "No files found in LLM response"
            mgr.record_429(model, "No files in response (empty)", 30)
            time.sleep(5)
            continue

        written = _write_project(project_dir, files)
        mgr.record_success(model)

        _CACHE[cache_key] = (project_id, time.time(), text)

        return {
            "success": True,
            "project_id": project_id,
            "cached": False,
            "files": written,
            "provider": model,
            "llm_calls": call_count,
        }

    return {
        "success": False,
        "error": f"Failed after {TOTAL_RETRIES} attempts | last: {last_error[:200]}",
        "project_id": project_id,
        "llm_calls": call_count,
    }


def _is_daily_quota(msg: str) -> bool:
    lowered = msg.lower()
    if "per day" in lowered or "daily" in lowered:
        return True
    if "quotaValue" in msg and "PerDay" in msg:
        return True
    if "tokens per day" in lowered:
        return True
    return False


def _extract_wait(msg: str) -> int:
    import ast
    try:
        parts = msg.split(". ", 1)
        if len(parts) > 1:
            d = ast.literal_eval(parts[1])
            for det in d.get("error", {}).get("details", []):
                rd = det.get("retryDelay", "")
                if rd:
                    m = re.match(r"(\d+)s", str(rd))
                    if m:
                        return int(m.group(1)) + 1
    except Exception:
        pass
    m = re.search(r"Please retry in ([\d.]+)s", msg)
    if m:
        return int(float(m.group(1))) + 1
    m = re.search(r"try again in ([\d.]+)s", msg)
    if m:
        return int(float(m.group(1))) + 1
    m = re.search(r"retryDelay.*?(\d+)s", msg)
    if m:
        return int(m.group(1)) + 1
    return 30
