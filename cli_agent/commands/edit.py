import os
from pathlib import Path
from cli_agent.core.client import ApiClient
from cli_agent.utils.logger import info, success, error, step, header, warn


def handle(client: ApiClient, project_path: str, prompt: str):
    header("SpringForge — Edit")

    abs_path = os.path.abspath(project_path)
    if not os.path.isdir(abs_path):
        error(f"Project path not found: {abs_path}")
        return False

    info(f"Project : {abs_path}")
    info(f"Request : {prompt}")

    result = client.edit(abs_path, prompt)

    if not result.get("success"):
        warn(f"Edit via API failed: {result.get('message', 'Unknown error')}")
        warn("Falling back to local regeneration...")
        return _local_edit_fallback(client, abs_path, prompt)

    success("Project modified successfully")
    changes = result.get("changes", [])
    for c in changes:
        info(f"  {c}")
    return True


def _local_edit_fallback(client: ApiClient, project_path: str, prompt: str) -> bool:
    combined = f"Modify the Spring Boot project at {project_path}. {prompt}"
    return handle(client, project_path, combined)
