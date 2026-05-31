import os
from pathlib import Path
from cli_agent.core.client import ApiClient
from cli_agent.utils.logger import info, success, error, step, header, warn


def handle(client: ApiClient, feature: str, project_path: str | None):
    header("SpringForge — Add Feature")

    if not project_path:
        error("No project path specified. Use --path <dir>")
        return False

    abs_path = os.path.abspath(project_path)
    if not os.path.isdir(abs_path):
        error(f"Project path not found: {abs_path}")
        return False

    info(f"Project : {abs_path}")
    info(f"Feature : {feature}")

    prompt = f"Add the following feature to the existing Spring Boot project: {feature}"
    result = client.edit(abs_path, prompt)

    if not result.get("success"):
        warn(f"API /edit unavailable: {result.get('message', 'Unknown error')}")
        warn("Generating new project with this feature included...")
        combined = f"Create a Spring Boot project that includes: {feature}"
        from cli_agent.commands.generate import handle as gen_handle
        return gen_handle(client, combined, os.path.dirname(abs_path))

    success(f"Feature added: {feature}")
    changes = result.get("changes", [])
    for c in changes:
        info(f"  {c}")
    return True
